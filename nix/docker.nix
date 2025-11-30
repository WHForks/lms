{
  lib,
  writeShellScriptBin,
  dockerTools,

  src,
  productionEnv,
  frontendAssets,
  staticAssets,

  uwsgi,
  bash,
  coreutils,
  findutils,
  gnugrep,
  gnused,
  postgresql,
  git,
  gosu,
  gettext,
  shadow,
  cacert,
  mailcap,
}:
let
  uwsgi-py = uwsgi.override {
    python3 = productionEnv;
    plugins = [ "python3" ];
  };

  pythonVersionShort = builtins.substring 0 4 productionEnv.python.version;

  entrypoint = writeShellScriptBin "entrypoint.sh" ''
    set -e

    cd /var/www/code

    echo "Running database migrations..."
    python manage.py migrate

    echo "Starting uWSGI..."
    export PYTHONPATH="${productionEnv}/lib/python${pythonVersionShort}/site-packages"
    exec ${lib.getExe uwsgi-py} --ini /etc/uwsgi.ini --show-config --static-map /static=/var/www/static --plugin python3
  '';
in
dockerTools.buildLayeredImage {
  name = "lms";
  tag = "latest";

  contents = [
    bash
    coreutils
    findutils
    gnugrep
    gnused

    productionEnv
    uwsgi-py

    postgresql
    git
    gosu
    gettext
    cacert
    mailcap

    entrypoint
  ];

  enableFakechroot = true;

  fakeRootCommands = ''
    mkdir -p /var/www/code /var/www/code/frontend /var/www/static /var/www/frontend-code/assets /etc /tmp

    cp -rL ${src}/* /var/www/code/
    cp -rL ${staticAssets}/static/* /var/www/static/
    cp -rL ${frontendAssets}/assets/* /var/www/frontend-code/assets/
    cp -L ${../docker-files/uwsgi.ini} /etc/uwsgi.ini

    ${shadow}/bin/groupadd --gid 101 appuser
    ${shadow}/bin/useradd --uid 101 --gid 101 --no-create-home --shell /bin/bash appuser

    ln -s /var/www/frontend-code/assets /var/www/code/frontend/assets
    ln -s /var/www/static /var/www/code/static

    chown -R appuser:appuser /var/www

    chmod 1777 /tmp
  '';

  config = {
    Env = [
      "PYTHONIOENCODING=UTF-8"
      "LC_ALL=C.UTF-8"
      "LANG=C.UTF-8"
      "PYTHONUNBUFFERED=1"
      "APP_USER=appuser"
      "DJANGO_STATIC_ROOT=/var/www/static"
      "WEBPACK_ASSETS_ROOT=/var/www/frontend-code/assets"
      "WEBPACK_ENVIRONMENT=prod"
      "SSL_CERT_FILE=${cacert}/etc/ssl/certs/ca-bundle.crt"
    ];
    ExposedPorts."8001/tcp" = { };
    WorkingDir = "/var/www/code";
    User = "appuser";
    Cmd = [ "${entrypoint}/bin/entrypoint.sh" ];
  };

  maxLayers = 120;
  meta.platforms = lib.platforms.linux;
}
