# `session_api_core.py` — Audit & Fix Tracker

**File under audit:** `rpa/open_rv/rpa_core/api/session_api_core.py`
**Date:** 2026-04-15
**Status:** In Progress

---

## Tracking Checklist

Work through each fix one at a time: understand -> discuss -> implement -> manually test -> commit -> push -> check off.

### Performance Fixes (Critical)
- [ ] **P1** — Remove redundant `setViewNode` in `create_clips` (2 full cache clears eliminated)
- [ ] **P2** — Remove redundant `setViewNode` in `__delete_clips_permanently` (2 full cache clears eliminated)
- [ ] **P3** — Add missing view node restore in `delete_playlists_permanently`
- [ ] **P4** — Deduplicate `__update_clip_nodes_in_playlist_node` calls in `set_attr_values` (N calls -> 1 per playlist)
- [ ] **P5** — Hoist `setCacheMode(CacheOff)` from per-clip to per-batch in `create_clips` (2N calls -> 2)
- [ ] **P6** — Wrap `set_active_clips` graph ops in `setCacheMode(CacheOff)` (prevents thread restart between calls)

### Bug Fixes (Crash/Data-Corruption Risk)
- [ ] **B1** — Fix IndexError in `__update_bg_retime_node` source_frame_lock path
- [x] **B2** — Move `SIG_ATTR_VALUES_CHANGED` emit outside loop in `clear_attr_values_at`
- [ ] **B3** — Fix `__set_bg_mode` skipping audio cleanup when bg is None

### Correctness Bugs
- [x] **B4** — Remove dead code in `set_attr_values`
- [x] **B5** — Remove side effect from `get_current_clip` getter
- [ ] **B6** — Add clip ownership validation in `set_active_clips`

### Minor Cleanups
- [ ] **M1** — Fix `move_clips_by_offset` losing attr changes across playlists
- [ ] **M2** — Limit `__redraw_annotations` to active clips only
- [x] **M3** — Remove duplicate import

### Suggested Fix Order

Work through issues in this order. Rationale: start with zero-risk warm-ups, then correctness bugs (isolated fixes with clear impact), then performance fixes (grouped by interaction), then minor cleanups.

| # | Issue | Why this position |
|---|-------|-------------------|
| 1 | **M3** | Zero-risk warm-up, verifies the edit-test-commit workflow |
| 2 | **B2** | Clear bug, simple one-line move, low coupling, observable fix |
| 3 | **B4** | Dead code removal, no behavior change |
| 4 | **B5** | Small getter fix, no downstream dependencies |
| 5 | **B1** | Crash fix, isolated to one code path - Continue from here|
| 6 | **B3** | Audio cleanup bug, moderate complexity but self-contained |
| 7 | **B6** | Defensive validation, low risk |
| 8 | **P1** | First perf fix — remove `setViewNode` in `create_clips`. Do before P5 since P5 changes the same method |
| 9 | **P5** | Hoist `setCacheMode` to batch level in `create_clips` — builds on P1's changes |
| 10 | **P2** | Same `setViewNode` removal pattern as P1, applied to `__delete_clips_permanently` |
| 11 | **P3** | Add missing view node restore in `delete_playlists_permanently` |
| 12 | **P4** | Deduplicate `__update_clip_nodes_in_playlist_node` in `set_attr_values` |
| 13 | **P6** | Wrap `set_active_clips` in `setCacheMode(CacheOff)` |
| 14 | **M1** | Cross-playlist attr bug, touches multiple concerns |
| 15 | **M2** | Limit annotation redraw scope |

---

## OpenRV Internals Reference

Understanding these internals is essential for evaluating the performance fixes.

### What `setViewNode()` does (C++ source: `IPGraph.cpp:954-982`)

```cpp
void IPGraph::setViewNode(IPNode* viewNode)
{
    if (m_viewNode == viewNode) return;   // No-op if same node
    beginGraphEdit();
    m_fbcache.lock();
    m_fbcache.clear();        // CLEARS ENTIRE FRAME BUFFER CACHE
    m_fbcache.unlock();
    m_topologyChanged = true;
    if (m_viewGroupNode) {
        m_viewGroupNode->disconnectInputs();
        m_viewGroupNode->setInputs1(viewNode);
    }
    m_viewNode = viewNode;
    m_viewNodeChangedSignal(viewNode);
    endGraphEdit();
}
```

**Cost:** Stops all caching threads, clears ALL cached frames, stops audio thread, restarts everything. This is the most expensive single operation available.

### What `setNodeInputs()` does (C++ source: `CommandsModule.cpp:4386-4448`)

```cpp
// Simplified
if (node->compareToInputs(inputNodes) != IdenticalResult) {
    graph.beginGraphEdit();    // Stops caching + audio threads
    node->setInputs(inputNodes);
    graph.endGraphEdit();      // Restarts caching + audio threads
}
```

**Cost:** Each call triggers a full thread shutdown/restart cycle. Has a built-in no-op check if inputs haven't changed.

### What `beginGraphEdit()`/`endGraphEdit()` do

- `beginGraphEdit()`: Stops caching threads, stops audio thread, sets `m_frameCacheInvalid = true`. **Nestable** (counter-based).
- `endGraphEdit()`: Only restarts threads when the counter reaches 0.
- **NOT exposed in Python/Mu API** — only used internally by C++. We cannot batch from Python.

### What `setCacheMode(CacheOff)` does

Sets `m_cacheMode = NeverCache`. When `endGraphEdit()` runs, it checks `if (m_cacheMode != NeverCache) redispatchCachingThread()`. So with caching off, `endGraphEdit()` skips the expensive thread restart. This is our main Python-level batching lever.

---

## Fix Details

---

### P1 — Remove redundant `setViewNode` in `create_clips`

**Location:** Lines 421-457

**Current code:**
```python
def create_clips(self, playlist_id, paths, index, ids):
    # ...
    view_node = commands.viewNode()
    commands.setViewNode(self.__empty_view)   # FULL CACHE CLEAR #1
    self.PRG_CLIPS_CREATION_STARTED.emit(num_of_clips_to_create)

    playlist = self.__session.get_playlist(playlist_id)
    playlist.create_clips(paths, ids, index)

    clips_created = 0
    for id, path in zip(ids, paths):
        self.__create_clip_nodes(id, path)    # Already uses setCacheMode(CacheOff) internally
        clips_created += 1
        self.PRG_CLIP_CREATED.emit(clips_created, num_of_clips_to_create)
    self.PRG_CLIPS_CREATION_COMPLETED.emit()

    # ... attr value setup, playlist node update ...

    commands.setViewNode(view_node)           # FULL CACHE CLEAR #2

    self.SIG_PLAYLIST_MODIFIED.emit(playlist_id)
    self.__update_current_clip()
    return ids
```

**Root cause:** The `setViewNode(empty_view)` was added to prevent OpenRV from evaluating the node graph during construction. But `__create_clip_nodes` already handles this by calling `setCacheMode(CacheOff)` at line 663. The `setViewNode` calls add two complete frame buffer cache clears with no protective benefit.

**Fix:** Remove lines 421-422 and line 457. The `setCacheMode(CacheOff)` inside `__create_clip_nodes` (or better, hoisted to this level per P5) provides the same protection without clearing the cache.

**After:**
```python
def create_clips(self, playlist_id, paths, index, ids):
    # ...
    self.PRG_CLIPS_CREATION_STARTED.emit(num_of_clips_to_create)

    playlist = self.__session.get_playlist(playlist_id)
    playlist.create_clips(paths, ids, index)

    clips_created = 0
    for id, path in zip(ids, paths):
        self.__create_clip_nodes(id, path)
        clips_created += 1
        self.PRG_CLIP_CREATED.emit(clips_created, num_of_clips_to_create)
    self.PRG_CLIPS_CREATION_COMPLETED.emit()

    # ... attr value setup, playlist node update ...

    self.SIG_PLAYLIST_MODIFIED.emit(playlist_id)
    self.__update_current_clip()
    return ids
```

**Manual test:**
1. Load a session with an existing playlist
2. Add 5+ clips to the playlist
3. Verify all clips appear, thumbnails load, and media plays correctly
4. Verify no black frames or missing media
5. Compare perceived speed of clip creation vs. before

---

### P2 — Remove redundant `setViewNode` in `__delete_clips_permanently`

**Location:** Lines 574-602

**Current code:**
```python
def __delete_clips_permanently(self, clip_ids):
    if len(clip_ids) == 0:
        return
    view_node = commands.viewNode()
    commands.setViewNode(self.__empty_view)    # FULL CACHE CLEAR #1
    # ... deletion loop with deleteNode/flushCachedNode ...
    self.SIG_CLIPS_DELETED.emit(clip_ids)
    self.PRG_CLIPS_DELETION_COMPLETED.emit()
    commands.setViewNode(view_node)            # FULL CACHE CLEAR #2
```

**Root cause:** Same pattern as P1. The `setViewNode` is used to prevent evaluation during deletion, but `flushCachedNode` already handles per-node cache invalidation. The two setViewNode calls add unnecessary full cache clears.

**Fix:** Replace `setViewNode` wrapper with `setCacheMode(CacheOff)` wrapper:

**After:**
```python
def __delete_clips_permanently(self, clip_ids):
    if len(clip_ids) == 0:
        return
    cache_mode = commands.cacheMode()
    commands.setCacheMode(commands.CacheOff)
    num_of_clips_to_delete = len(clip_ids)
    num_of_clips_deleted = 0
    self.PRG_CLIPS_DELETION_STARTED.emit(num_of_clips_to_delete)
    for clip_id in clip_ids:
        # ... same deletion logic ...
    self.SIG_CLIPS_DELETED.emit(clip_ids)
    self.PRG_CLIPS_DELETION_COMPLETED.emit()
    commands.setCacheMode(cache_mode)
```

**Manual test:**
1. Create a playlist with 5+ clips
2. Delete clips one at a time and in bulk
3. Verify remaining clips still display correctly
4. Verify no crashes or black viewport after deletion

---

### P3 — Add missing view node restore in `delete_playlists_permanently`

**Location:** Lines 120-142

**Current code:**
```python
def delete_playlists_permanently(self, ids):
    commands.setViewNode(self.__empty_view)  # Sets to empty but NEVER restores
    fg_playlist = self.get_fg_playlist()
    for playlist_id in ids:
        # ... delete playlist nodes ...
    self.__session.delete_playlists_permanently(ids)
    self.__map_default_playlist_if_created()
    self.__set_bg_mode(self.__session.viewport.bg_mode)
    # ... signals ...
```

**Root cause:** Unlike `create_clips` and `__delete_clips_permanently`, this method never restores the view node. After deletion, the view stays pointed at `__empty_view` until some other operation happens to call `__set_fg_pl_seq_grp_to_view_node()`.

Note: We can't simply remove the `setViewNode` here (unlike P1/P2) because this method deletes entire playlist sequence group nodes — the current view node might be one of them. Pointing to empty first is intentional safety.

**Fix:** The method already calls `__set_fg_pl_seq_grp_to_view_node()` indirectly through `__set_bg_mode` (which calls it when mode==0). However, this only works if bg_mode is 0. Add explicit restoration:

```python
def delete_playlists_permanently(self, ids):
    commands.setViewNode(self.__empty_view)
    fg_playlist = self.get_fg_playlist()
    for playlist_id in ids:
        # ... delete playlist nodes ...
    self.__session.delete_playlists_permanently(ids)
    self.__map_default_playlist_if_created()
    self.__set_fg_pl_seq_grp_to_view_node()  # Explicitly restore view node
    self.__set_bg_mode(self.__session.viewport.bg_mode)
    # ... rest unchanged ...
```

**Manual test:**
1. Create 3 playlists with clips
2. Delete one playlist that is NOT the foreground
3. Verify the viewport still shows the foreground playlist content
4. Delete the foreground playlist
5. Verify the viewport switches to the next available playlist

---

### P4 — Deduplicate `__update_clip_nodes_in_playlist_node` in `set_attr_values`

**Location:** Lines 1113-1166

**Current code (inside the loop):**
```python
for attr_value in attr_values:
    playlist_id, clip_id, attr_id, value = attr_value
    # ...
    if attr_id in ("key_in", "key_out"):
        self.__update_retime_node(clip_id)
        self.__update_clip_nodes_in_playlist_node(playlist)  # Called per attr!
    if attr_id in ("dissolve_start", "dissolve_length"):
        self.__update_clip_nodes_in_playlist_node(playlist)  # Called per attr!
    # ...
```

**Root cause:** If you set `key_in` and `key_out` for 10 clips in one call, `__update_clip_nodes_in_playlist_node` is called 20 times. Each call invokes `setNodeInputs` which triggers a full thread shutdown/restart. Only 1 call per unique playlist is needed since the final node graph state is the same.

**Fix:**
```python
def set_attr_values(self, attr_values):
    # ...
    playlists_needing_node_update = set()

    for attr_value in attr_values:
        playlist_id, clip_id, attr_id, value = attr_value
        # ... existing attr set logic ...
        if attr_id in ("key_in", "key_out"):
            self.__update_retime_node(clip_id)
            playlists_needing_node_update.add(playlist_id)
        if attr_id in ("dissolve_start", "dissolve_length"):
            playlists_needing_node_update.add(playlist_id)
        # ... rest of loop body (dependent attrs, progress signals) ...

    # Deferred: one setNodeInputs call per playlist
    for pid in playlists_needing_node_update:
        pl = self.__session.get_playlist(pid)
        if pl:
            self.__update_clip_nodes_in_playlist_node(pl)

    # ... timeline update, signal emission ...
```

**Manual test:**
1. Load a playlist with 10+ clips
2. Select all clips and change key_in or key_out in bulk
3. Verify the timeline updates correctly for all clips
4. Verify cross-dissolve transitions still work after changing dissolve_start/dissolve_length
5. Compare speed of bulk attr changes vs. before

---

### P5 — Hoist `setCacheMode(CacheOff)` from per-clip to per-batch

**Location:** `create_clips` (lines 410-457) and `__create_clip_nodes` (lines 647-731)

**Current code in `__create_clip_nodes`:**
```python
def __create_clip_nodes(self, id, path):
    clip = self.__session.get_clip(id)
    # ...
    cache_mode = commands.cacheMode()          # Save per clip
    commands.setCacheMode(commands.CacheOff)    # Disable per clip
    # ... create nodes ...
    commands.setCacheMode(cache_mode)           # Restore per clip
```

**Root cause:** For N clips, this calls `setCacheMode` 2N times. The save/restore should happen once around the entire batch.

**Fix in `create_clips`:**
```python
def create_clips(self, playlist_id, paths, index, ids):
    # ...
    cache_mode = commands.cacheMode()
    commands.setCacheMode(commands.CacheOff)
    try:
        self.PRG_CLIPS_CREATION_STARTED.emit(num_of_clips_to_create)
        playlist = self.__session.get_playlist(playlist_id)
        playlist.create_clips(paths, ids, index)
        for id, path in zip(ids, paths):
            self.__create_clip_nodes(id, path)
            # ...
        self.__update_clip_nodes_in_playlist_node(playlist)
        # ... play_order updates ...
    finally:
        commands.setCacheMode(cache_mode)
    # Signals emitted AFTER cache is restored
    self.SIG_ATTR_VALUES_CHANGED.emit(attr_values_list)
    self.SIG_PLAYLIST_MODIFIED.emit(playlist_id)
    self.__update_current_clip()
    return ids
```

**Fix in `__create_clip_nodes`:** Remove lines 662-663 and 731 (the per-clip cache mode save/restore).

**Manual test:** Same as P1 — create 5+ clips, verify correct loading and playback.

---

### P6 — Wrap `set_active_clips` graph ops in `setCacheMode(CacheOff)`

**Location:** Lines 505-524

**Current code:**
```python
def set_active_clips(self, playlist_id, clip_ids):
    current_frame = commands.frame()
    playlist = self.__session.get_playlist(playlist_id)
    playlist.set_active_clips(clip_ids)
    if self.__session.viewport.bg is None:
        self.__session.update_activated_clip_indexes()
    else:
        self.__session.match_fg_bg_clip_indexes()
        self.__update_clip_nodes_in_playlist_node(bg_playlist)  # Thread restart #1
    self.__update_clip_nodes_in_playlist_node(playlist)          # Thread restart #2
    # ... signals, frame update ...
```

**Root cause:** This is the **hot path for rapid clip switching**. When BG is active, two `setNodeInputs` calls each trigger their own thread shutdown/restart cycle. Between the two calls, the caching thread may restart and begin evaluating an incomplete graph state.

**Fix:**
```python
def set_active_clips(self, playlist_id, clip_ids):
    current_frame = commands.frame()
    playlist = self.__session.get_playlist(playlist_id)
    playlist.set_active_clips(clip_ids)

    cache_mode = commands.cacheMode()
    commands.setCacheMode(commands.CacheOff)
    try:
        if self.__session.viewport.bg is None:
            self.__session.update_activated_clip_indexes()
        else:
            self.__session.match_fg_bg_clip_indexes()
            self.__update_clip_nodes_in_playlist_node(
                self.__session.get_playlist(self.__session.viewport.bg))
        self.__update_clip_nodes_in_playlist_node(playlist)
    finally:
        commands.setCacheMode(cache_mode)

    if self.__timeline_api:
        self.__timeline_api._playlist_seq_modified(playlist_id)
    self.SIG_PLAYLIST_MODIFIED.emit(playlist_id)
    self.__update_current_clip()
    self.__set_current_frame(current_frame)
```

**Manual test:**
1. Load a session with 20+ clips
2. Rapidly click through clips in the session manager (click every ~100ms)
3. Verify reduced stutter/lag compared to before
4. Test with BG playlist active — switch between clips rapidly
5. Verify the correct clip is always displayed after switching stops

---

### B1 — Fix IndexError in `__update_bg_retime_node`

**Location:** Lines 283-302

**Current code:**
```python
elif self.__session.viewport.source_frame_lock == 1:
    # ...
    for fg_clip_id, bg_clip_id in zip(fg_clip_ids, bg_clip_ids):
        fg_frames, bg_frames = ...
        final_bg_frames = []
        fg_i, bg_i = 0, 0
        while fg_i < len(fg_frames):
            while fg_i < len(fg_frames) and fg_frames[fg_i] < bg_frames[bg_i]:
                final_bg_frames.append(bg_frames[bg_i])
                fg_i += 1
            while bg_i+1 < len(bg_frames) and fg_frames[fg_i] > bg_frames[bg_i]:
                #                              ^^^^^^^^^^^^^^^^ fg_i may be OOB!
                bg_i += 1
            final_bg_frames.append(bg_frames[bg_i])
            fg_i = fg_i+1
```

**Root cause:** The first inner `while` loop increments `fg_i` until `fg_i >= len(fg_frames)`. Then the second inner `while` loop accesses `fg_frames[fg_i]` without bounds check. If the first loop consumed all remaining fg_frames, this is an `IndexError`.

**Fix:** Add `fg_i < len(fg_frames)` guard to the second while condition:

```python
while bg_i+1 < len(bg_frames) and fg_i < len(fg_frames) and fg_frames[fg_i] > bg_frames[bg_i]:
    bg_i += 1
```

Also add a guard before line 298 to handle the case where fg_i is exhausted:
```python
if fg_i >= len(fg_frames):
    break
final_bg_frames.append(bg_frames[bg_i])
fg_i = fg_i+1
```

**Manual test:**
1. Set up FG and BG playlists where FG clip has a shorter frame range that starts earlier than BG
2. Enable source_frame_lock
3. Verify no crash and correct frame synchronization

---

### B2 — Move signal emit outside loop in `clear_attr_values_at`

**Location:** Lines 1268-1294

**Current code:**
```python
def clear_attr_values_at(self, clear_at):
    clip_attr_values = []
    for attr_value_at in clear_at:
        # ... process attr ...
        clip_attr_values.append((playlist_id, clip_id, attr_id, attr_value))

        self.SIG_ATTR_VALUES_CHANGED.emit(clip_attr_values)  # INSIDE loop!
    return True
```

**Root cause:** The signal is emitted inside the loop. On iteration 1, it emits `[A]`. On iteration 2, it emits `[A, B]`. On iteration 3, it emits `[A, B, C]`. Listeners process `A` three times, `B` twice, etc.

**Fix:** Move emit outside the loop:

```python
def clear_attr_values_at(self, clear_at):
    clip_attr_values = []
    for attr_value_at in clear_at:
        # ... process attr ...
        clip_attr_values.append((playlist_id, clip_id, attr_id, attr_value))

    self.SIG_ATTR_VALUES_CHANGED.emit(clip_attr_values)  # After loop
    return True
```

**Manual test:**
1. Set keyable attribute values at multiple keys for a clip
2. Clear multiple keys at once
3. Verify the attribute UI updates correctly (no duplicates, no flicker)

---

### B3 — Fix `__set_bg_mode` skipping audio cleanup when bg is None

**Location:** Lines 855-878

**Current code:**
```python
def __set_bg_mode(self, mode):
    if mode == 0:
        runtime.eval("require rv_state_mngr; rv_state_mngr.enable_frame_change_mouse_events();", [])
        if self.__is_wipe_mode():
            self.__toggle_wipe_mode()
        self.__set_fg_pl_seq_grp_to_view_node()
    if self.__session.viewport.bg is None:
        return                                    # Skips audio cleanup for mode==0!
    frame = commands.frame()
    if mode != 0:
        self.set_mix_mode(0)
    if mode == 1: self.__set_bg_mode_wipe()
    # ... other modes ...
    commands.setFrame(frame)
    self.__set_bg_mode_audio_input(mode)          # Never reached when bg is None
```

**Root cause:** When mode==0 and bg is None, the `return` at the bg check skips `__set_bg_mode_audio_input(mode)`. The audio input may remain configured for a now-removed BG playlist.

**Fix:** Complete mode==0 cleanup (including audio) before the bg guard:

```python
def __set_bg_mode(self, mode):
    if mode == 0:
        runtime.eval(
            "require rv_state_mngr;"
            "rv_state_mngr.enable_frame_change_mouse_events();", [])
        if self.__is_wipe_mode():
            self.__toggle_wipe_mode()
        self.__set_fg_pl_seq_grp_to_view_node()
        self.__set_bg_mode_audio_input(mode)
        return  # mode 0 cleanup complete, bg not needed
    if self.__session.viewport.bg is None:
        return
    frame = commands.frame()
    self.set_mix_mode(0)
    if mode == 1: self.__set_bg_mode_wipe()
    elif mode == 2: self.__set_bg_mode_side_by_side()
    elif mode == 3: self.__set_bg_mode_top_bottom()
    elif mode == 4: self.__set_bg_mode_pip()
    commands.setFrame(frame)
    self.__set_bg_mode_audio_input(mode)
```

**Manual test:**
1. Set up FG and BG playlists with wipe mode
2. Remove the BG playlist (set bg to None)
3. Set bg_mode to 0
4. Verify audio plays from FG playlist correctly (not silent/stale)

---

### B4 — Remove dead code in `set_attr_values`

**Location:** Lines 1160-1164

**Current code:**
```python
# timeline update for when frame control attrs change
if any(attr_value[0] == self.__session.viewport.fg and \
    attr_value[2] in ("key_in", "key_out") for attr_value in attr_values):
    playlist = self.__session.get_playlist(self.__session.viewport.fg)
    # playlist assigned but never used
```

**Fix:** Delete the entire block (4 lines including comment).

**Manual test:** No behavior change expected. Verify key_in/key_out changes still work correctly.

---

### B5 — Remove side effect from `get_current_clip`

**Location:** Lines 822-828

**Current code:**
```python
def get_current_clip(self):
    playlist = self.__session.get_playlist(self.__session.viewport.fg)
    if playlist is None or len(playlist.clip_ids) == 0:
        self.__session.viewport.current_clip = None  # Side effect in getter!
    clip = self.__session.get_clip(self.__session.viewport.current_clip)
    if clip: return self.__session.viewport.current_clip
    return
```

**Root cause:** Getters should not mutate state. The `__update_current_clip()` method already handles state synchronization and is called from all mutating code paths.

**Fix:**
```python
def get_current_clip(self):
    playlist = self.__session.get_playlist(self.__session.viewport.fg)
    if playlist is None or len(playlist.clip_ids) == 0:
        return None
    clip = self.__session.get_clip(self.__session.viewport.current_clip)
    if clip:
        return self.__session.viewport.current_clip
    return None
```

**Manual test:**
1. Load a session, verify `get_current_clip` returns the correct clip
2. Delete all clips, verify `get_current_clip` returns None
3. Add clips back, verify it works correctly again

---

### B6 — Add clip ownership validation in `set_active_clips`

**Location:** Line 505

**Fix:** Add validation at the start of the method:

```python
def set_active_clips(self, playlist_id, clip_ids):
    playlist = self.__session.get_playlist(playlist_id)
    if playlist is None:
        return
    valid_clip_ids = set(playlist.clip_ids)
    for clip_id in clip_ids:
        if clip_id not in valid_clip_ids:
            print(f"Warning: Clip {clip_id} does not belong to playlist {playlist_id}")
            return
    # ... rest of method ...
```

**Manual test:** This is defensive — verify normal clip activation still works. Hard to trigger accidentally in production.

---

### M1 — Fix `move_clips_by_offset` losing attr changes across playlists

**Location:** Lines 552-571

**Current code:**
```python
def move_clips_by_offset(self, offset, ids):
    to_move = {}
    for id in ids:
        clip = self.__session.get_clip(id)
        to_move.setdefault(clip.playlist_id, []).append(clip.id)

    attr_values = []
    for playlist_id, clip_ids in to_move.items():
        playlist = self.__session.get_playlist(playlist_id)
        playlist.move_clips_by_offset(offset, clip_ids)
        attr_values.clear()   # BUG: clears accumulated values from previous playlists!
        for play_order, clip_id in enumerate(playlist.clip_ids):
            # ... accumulate play_order changes ...
        self.SIG_ATTR_VALUES_CHANGED.emit(attr_values)
        # ...
```

**Fix:** Don't clear attr_values inside the loop, or use a separate list per playlist:

```python
all_attr_values = []
for playlist_id, clip_ids in to_move.items():
    playlist = self.__session.get_playlist(playlist_id)
    playlist.move_clips_by_offset(offset, clip_ids)
    for play_order, clip_id in enumerate(playlist.clip_ids):
        clip = self.__session.get_clip(clip_id)
        value = play_order + 1
        clip.set_attr_value("play_order", value)
        all_attr_values.append((playlist.id, clip.id, "play_order", value))
    self.__update_clip_nodes_in_playlist_node(playlist)
    self.SIG_PLAYLIST_MODIFIED.emit(playlist.id)
self.SIG_ATTR_VALUES_CHANGED.emit(all_attr_values)
return True
```

**Manual test:** Move clips by offset when clips span multiple playlists. Verify play_order is correct in all playlists.

---

### M2 — Limit `__redraw_annotations` to active clips only

**Location:** Lines 604-611

**Current code:**
```python
def __redraw_annotations(self):
    playlist_id = self.__session.viewport.fg
    playlist = self.__session.get_playlist(playlist_id)
    for clip_id in playlist.clip_ids:       # ALL clips, even inactive
        # ... redraw annotations ...
```

**Fix:** Change `playlist.clip_ids` to `playlist.active_clip_ids`.

**Manual test:** Switch foreground playlists. Verify annotations display correctly on active clips.

---

### M3 — Remove duplicate import

**Location:** Lines 1 and 14

Both import `from rpa.session_state.session import Session`. Remove line 14.

**Manual test:** Verify the file still imports and runs correctly.

---

## Expected Performance Impact Summary

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| `create_clips` (N clips) | 2 `setViewNode` (full cache clear) + 2N `setCacheMode` | 0 `setViewNode` + 2 `setCacheMode` | Eliminates 2 full cache clears |
| `delete_clips_permanently` | 2 `setViewNode` (full cache clear) | 0 `setViewNode` + 2 `setCacheMode` | Eliminates 2 full cache clears |
| `set_active_clips` (with BG) | 2 `setNodeInputs` with caching active | 2 `setNodeInputs` with caching off | Prevents thread restart between calls |
| `set_attr_values` (N attrs, M playlists) | N `setNodeInputs` | M `setNodeInputs` | Up to Nx reduction |
