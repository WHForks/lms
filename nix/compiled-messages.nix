{
  stdenvNoCC,
  pythonEnv,
  src,
  tzdata,
  gettext,
}:
stdenvNoCC.mkDerivation {
  inherit src;
  pname = "lms-compiled-messages";
  version = "0-unstable";

  nativeBuildInputs = [
    pythonEnv
    gettext
  ];

  buildPhase = ''
    runHook preBuild

    python manage.py compilemessages

    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall

    mkdir -p $out
    cp -r locale $out/

    runHook postInstall
  '';

  env = {
    DJANGO_SETTINGS_MODULE = "lms.settings.extended";
    ENV_FILE = "${src}/lms/settings/.env.example";
    PYTHONTZPATH = "${tzdata}/share/zoneinfo";
    DJANGO_SECRET_KEY = "build-time-secret-key-not-for-production";
    DATABASE_URL = "sqlite:///:memory:";
  };

  doFixup = false;
}
