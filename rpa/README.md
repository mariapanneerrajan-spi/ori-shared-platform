## Objective:

To empower VFX and Animation studios to use their custom built review workflows and tools across any review-playback system (such as OpenRV or xStudio),
RPA provides a unified collection of **API modules** and **widgets**.

RPA is designed for pipeline developers to build their review workflows and tools once and deploy them seamlessly across any review-playback system that supports the RPA implementation.

RPA is an abstraction layer between the review widgets you create and the review-playback systems you use.

## Documentation:

[RPA Documentation](https://ori-shared-platform.readthedocs.io/en/latest/)

## Contents:

- **RPA API Modules:**
Collection of RPA api modules that help manipulate an RPA review session.
- **RPA Widgets:**
Collection of rpa widgets that facilalte a complete review workflow.
- **Open RV Pkgs:**
Prebuilt packages for adding rpa(Review Plugin API) and rpa widgets into Open RV.

## Build and Install (dev mode)

Point `RV_HOME` environment variable to your OpenRV installation, then from the repo root:

```
python rpa/dev_setup.py build          # build rvpkgs into rpa/local_install/ (no RV_HOME needed)
python rpa/dev_setup.py install-deps   # install Python deps into OpenRV's Python (needs RV_HOME)
python rpa/dev_setup.py all            # both
```

Launch the app:

```
# Linux/Mac
./rpa/launch_app

# Windows
rpa\launch_app.bat
```

Both launchers require `RV_HOME` to be set.

## Read the Docs Publish Workflow:

1. If you want to update the documentation you can update the sphinx source here,
`>> ./rpa/docs/source`

2. If you want to build and locally test your documentation you can run the following commands,
`>> cd ./rpa/docs; make clean; make html`

3. Kindly make sure to remove your `>> ./rpa/docs/build` directory before pushing.

3. Update the following read the docs config file if needed,
`./.readthedocs.yaml`

5. Now when you push to main, your sphinx html documention will be generated and publised to,
**[https://ori-shared-platform.readthedocs.io/en/latest/](https://ori-shared-platform.readthedocs.io/en/latest/)**
