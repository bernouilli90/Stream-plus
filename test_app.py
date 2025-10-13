try:
    from app import app, APP_VERSION
    print('Version:', APP_VERSION)
    print('App created successfully')
    with app.app_context():
        print('App context works')
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()