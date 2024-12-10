echo Running commans to setup the layer...
mkdir common\python\mod_medicaid
mkdir common\python\lib\python3.11\site-packages
copy lambda\mod_medicaid\* common\python\mod_medicaid\
pip install -r lambda\requirements.txt --target common\python\lib\python3.11\site-packages
cd common
tar.exe -a -cf python.zip python
cd ..
rmdir /S /Q common\python
