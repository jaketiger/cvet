module.exports = {
  apps : [{
    name   : "megacvet-app",
    
    // ----- ИЗМЕНЕНИЕ ЗДЕСЬ -----
    // Мы указываем точный путь к исполняемому файлу gunicorn
    script : "/home/www_jaketiger/megacvet/venv/bin/gunicorn",

    interpreter: "none",
    args   : "--workers 3 --bind unix:/home/www_jaketiger/megacvet/megacvet_project.sock megacvet_project.wsgi:application",

    
    // Эту строку теперь можно удалить, так как путь к исполняемому файлу уже содержит venv,
    // но ее можно и оставить, вреда не будет.
    // interpreter: "/home/www_jaketiger/megacvet/venv/bin/python",

    env: {
      "DJANGO_SECRET_KEY": "django-insecure-8$n0drft1v!r0ox=rqgcc&2x00&yzt@#y%(t87p21my2aaqdry",
      "DJANGO_DEBUG": "False",
      "DATABASE_URL": "postgres://www_jaketiger:Windows78@localhost:5432/megacvet_db"
    }
  }]
}
