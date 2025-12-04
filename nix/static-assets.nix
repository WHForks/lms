{
  stdenvNoCC,
  pythonEnv,
  src,
  frontendAssets,
  compiledMessages,
  tzdata,
  gettext,
}:
stdenvNoCC.mkDerivation {
  inherit src;

  pname = "lms-static-assets";
  version = "0-unstable";

  nativeBuildInputs = [
    pythonEnv
    gettext
  ];

  buildPhase = ''
    runHook preBuild

    cp -r ${compiledMessages}/locale ./
    mkdir -p "$DJANGO_STATIC_ROOT"
    python manage.py collectstatic --noinput --ignore "webpack-stats-v*.json"

    runHook postBuild
  '';

  env = {
    DJANGO_SETTINGS_MODULE = "lms.settings.extended";
    ENV_FILE = "${src}/lms/settings/.env.example";
    WEBPACK_ASSETS_ROOT = "${frontendAssets}/assets";
    WEBPACK_ENVIRONMENT = "prod";
    PYTHONTZPATH = "${tzdata}/share/zoneinfo";
    DJANGO_SECRET_KEY = "build-time-secret-key-not-for-production";
    DATABASE_URL = "sqlite:///:memory:";
    DJANGO_STATIC_ROOT = "${placeholder "out"}/static";
  };

  doFixup = false;
}
