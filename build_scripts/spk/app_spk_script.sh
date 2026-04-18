#!/bin/bash

#install python dependencies from the spk build script for the
#different python interpreter used by the plugin under spfs
export PYTHONPATH=""
export RV_HOME=/spfs/lib/openrv
RV_PYTHON="$RV_HOME/bin/python3"

${RV_PYTHON} -m pip install playwright
${RV_PYTHON} -m pip install scipy==1.13.1
${RV_PYTHON} -m pip install OpenImageIO==3.0.4
${RV_PYTHON} -m pip install imageio==2.37.0
echo "SUCCESS: RV Python dependencies installed!"

if [ "$RPA_APP_SPK_INSTALL" == "1" ]; then

    RV_PYTHON="$RV_HOME/bin/python3"
    RV_PY_DIR=`${RV_PYTHON} -BEs -c 'import site; print(site.getsitepackages()[0])'`
    SPK_PY_DIR=`python -BEs -c 'import site; print(site.getsitepackages()[0])'`
    for PY_DIR in $RV_PY_DIR $SPK_PY_DIR; do
        rm -rf $PY_DIR/rpa
        mkdir -p $PY_DIR/rpa/
        rsync -av --exclude='./.*' ./rpa/* $PY_DIR/rpa/
        echo "SUCCESS: RPA synced to $PY_DIR!"

        rm -rf $PY_DIR/rpa_app
        mkdir -p $PY_DIR/rpa_app
        rsync -av --exclude='./rpa_app/.*' ./rpa_app/* $PY_DIR/rpa_app/
        echo "SUCCESS: rpa_app synced to $PY_DIR!"

        rm -rf $PY_DIR/spi_rpa_app
        mkdir -p $PY_DIR/spi_rpa_app
        rsync -av --exclude='./spi_rpa_app/.*' ./spi_rpa_app/* $PY_DIR/spi_rpa_app/
        echo "SUCCESS: spi_rpa_app synced to $PY_DIR!"

        rm -rf $PY_DIR/rpa_app_plugins
        mkdir -p $PY_DIR/rpa_app_plugins
        rsync -av --exclude='./rpa_app_plugins/.*' ./rpa_app_plugins/* $PY_DIR/rpa_app_plugins/
        echo "SUCCESS: rpa_app_plugins synced to $PY_DIR!"
    done

    export APP_RV_SUPPORT_PATH=$RV_HOME/rpa_app
    rm -rf $APP_RV_SUPPORT_PATH
    mkdir -p $APP_RV_SUPPORT_PATH/Packages/

    export RV_SUPPORT_PATH=$RV_HOME/rpa
    rm -rf $RV_SUPPORT_PATH
    mkdir -p $RV_SUPPORT_PATH/Packages/
    ./rpa/build_scripts_spi/_install_rpa_core_pkg.sh
    echo "SUCCESS: RPA Core Package installed on RV!"

    export RV_SUPPORT_PATH=$RV_SUPPORT_PATH:$APP_RV_SUPPORT_PATH
    ./rpa_app/core/open_rv/install.sh

    cp ./rpa_app/rpa_app /spfs/bin/open_rpa_app
    cp ./spi_rpa_app/rpa_app /spfs/bin/rpa_app

fi
