class DbidMapper:
    def __init__(self):
        self.__dbid_to_clips = {}
        self.__clip_to_dbid = {}
        self.__clip_to_feedback = {}

    def map(self, clip, dbid):
        self.__clip_to_dbid[clip] = dbid
        self.__dbid_to_clips.setdefault(dbid, []).append(clip)

    def map_feedback(self, clip_id, feedback):
        self.__clip_to_feedback[clip_id] = feedback

    def get_dbid(self, clip):
        return self.__clip_to_dbid.get(clip, (None, None))

    def get_clips(self, dbid):
        return self.__dbid_to_clips.get(dbid, [])

    def get_feedback(self, clip_id):
        return self.__clip_to_feedback.get(clip_id, None)

    def unmap(self, clip):
        if clip not in self.__clip_to_dbid:
            return
        dbid = self.__clip_to_dbid[clip]
        del self.__clip_to_dbid[clip]
        self.__dbid_to_clips[dbid].remove(clip)
        if len(self.__dbid_to_clips[dbid]) == 0:
            del self.__dbid_to_clips[dbid]

    def unmap_feedback(self, clip):
        if clip not in self.__clip_to_feedback:
            return
        del self.__clip_to_feedback[clip]

    def is_mapped(self, clip):
        return clip in self.__clip_to_dbid

    def is_feedback(self, clip):
        return clip in self.__clip_to_feedback

    def clear(self):
        self.__clip_to_dbid.clear()
        for clips in self.__dbid_to_clips.values():
            clips.clear()
        self.__dbid_to_clips.clear()
        self.__clip_to_feedback.clear()
