{
  src,
  pythonEnv,
  databaseWithMigrations,

  stdenvNoCC,
  writableTmpDirAsHomeHook,
  postgresql,
  redis,
}:
stdenvNoCC.mkDerivation {
  pname = "lms-pytest";
  version = "0-unstable";
  inherit src;

  nativeBuildInputs = [
    pythonEnv
    writableTmpDirAsHomeHook
    postgresql
    redis
  ];

  ENV_FILE = "lms/settings/.env.example";

  env = {
    REDIS_HOST = "127.0.0.1";
    REDIS_PORT = "6379";
    REDIS_SSL = "false";
    REDIS_PASSWORD = "";
  };

  buildPhase = ''
    runHook preBuild

    DATABASE_DIR=$(mktemp -d)
    cp -r ${databaseWithMigrations}/postgres/* "$DATABASE_DIR"
    chmod -R u+w "$DATABASE_DIR"

    pg_ctl -D "$DATABASE_DIR" -o "-k $DATABASE_DIR -h \"\"" start

    psql -h "$DATABASE_DIR" -d cscdb -c "ALTER USER csc CREATEDB;"

    REDIS_DIR=$(mktemp -d)

    redis-server --port 6379 --bind 127.0.0.1 --dir "$REDIS_DIR" --appendonly yes &
    REDIS_PID=$!

    for i in {1..30}; do
      if redis-cli ping 2>/dev/null | grep -q PONG; then
        break
      fi
      sleep 0.1
    done

    export DATABASE_URL="postgresql://csc@/cscdb?host=$DATABASE_DIR"

    pytest -vx --deselect=lms/apps/learning/study/tests/test_views.py::test_view_student_assignment_jba_no_submissions_help_text

    kill $REDIS_PID
    pg_ctl -D "$DATABASE_DIR" stop

    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    touch $out
    runHook postInstall
  '';

  dontFixup = true;
}
