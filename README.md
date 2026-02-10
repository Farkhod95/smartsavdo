# INSTALL & SETUP INSTRUCTIONS

    to clone project open terminal & write: git clone https://gitlab.com/,
    then: cd ,
    if you have got other branch than master, write: git checkout your_branch

#### 1. Create a virtual environment to isolate our package dependencies locally

    pip install virtualenv
    python -m venv env

    source env/bin/activate for Linux/MacOS
    env\Scripts\activate for Windows

    deactivate

#### 3. Install requirements

    pip install -r requirements.txt

#### 4. Migrate

    python manage.py makemigrations
    python manage.py migrate

#### 5. Create superuser

    python manage.py createsuperuser

#### 6. Run server
    env\Scripts\activate

    celery -A main beat --loglevel=info 
    celery -A main worker --loglevel=info --pool=solo 

    python manage.py runserver

#### 7. Enjoy

    http://localhost:8000/api/v1/
    http://localhost:8000/admin/

#### 8. Server Hostland
    cd ~/www/optivora.com
    python3.11 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip setuptools wheel
    pip --version   # yangilanganini ko‘rasiz
    pip install -r requirements.txt
    python -m django --version   # 4.2.13 chiqishi kerak


#### 9. Elegantdan malumotlarni import qilish 
    # Ishga tushirish
        python manage.py import_product_models
    # Agar elegant_id bo‘yicha borlarini yangilab ketsin desangiz:
        python manage.py import_product_models --update
    
    # model_types boyicha import
        python manage.py import_product_model_types 

    # import_product_type boyicha import
        python manage.py import_product_type_sizes --update
    
    # import_products_from_warehouse 
        python manage.py import_products_from_warehouse --path inventory/data/warehouse.json



    