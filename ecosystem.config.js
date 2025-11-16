module.exports = {
  apps : [
    {
      name   : "cvet",
      script : "/var/www/cvet/venv/bin/gunicorn",
      args   : "--workers 3 --bind unix:/var/www/cvet/gunicorn.sock megacvet_project.wsgi:application",
      cwd    : "/var/www/cvet/",
      interpreter: "/var/www/cvet/venv/bin/python",
    },
    {
      name   : "cvet-worker",
      script : "/var/www/cvet/manage.py",
      args   : "qcluster",
      cwd    : "/var/www/cvet/",
      interpreter: "/var/www/cvet/venv/bin/python",
    }
  ]
};
