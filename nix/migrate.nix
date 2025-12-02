{
  src,
  pythonEnv,

  stdenvNoCC,
  writableTmpDirAsHomeHook,
  postgresql,
  lib,
  stdenv,
}:
stdenvNoCC.mkDerivation {
  pname = "migrations-db";
  version = "0-unstable";
  inherit src;

  nativeBuildInputs = [
    pythonEnv
    writableTmpDirAsHomeHook
    postgresql
  ];

  ENV_FILE = "lms/settings/.env.example";

  buildPhase = ''
    runHook preBuild
    DATABASE_DIR=$(mktemp -d)

    initdb -D "$DATABASE_DIR"

    pg_ctl -D "$DATABASE_DIR" -o "-k $DATABASE_DIR -h \"\"" start

    createuser -h "''$DATABASE_DIR" csc
    createdb -h "''$DATABASE_DIR" -O csc cscdb
    export DATABASE_URL="postgresql://csc@/cscdb?host=$DATABASE_DIR"

    python manage.py migrate

    pg_ctl -D "$DATABASE_DIR" stop
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p $out/
    cp -r $DATABASE_DIR $out/postgres
    runHook postInstall
  '';

  dontFixup = true;

  # PostgreSQL initdb requires System V shared memory which is blocked
  # by the macOS sandbox. This derivation can only be built on Linux.
  meta = {
    broken = stdenv.isDarwin;
    platforms = lib.platforms.unix;
  };
}
