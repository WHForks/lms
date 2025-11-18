{
  lib,
  stdenvNoCC,
  nodejs_20,
  yarn-berry_4,
  root,
  webpack-environment ? "prod",
}:
let
  nodejs = nodejs_20;
  yarn-berry = yarn-berry_4;
in
stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "frontend-assets";
  version = "0-unstable";

  src = lib.fileset.toSource {
    inherit root;
    fileset = lib.fileset.unions (
      map (path: root + path) [
        "/package.json"
        "/yarn.lock"
        "/.yarnrc.yml"
        "/babel.config.js"
        "/tsconfig.json"
        "/tsconfig.build.json"
        "/webpack/"
        "/src/"
        "/assets/"
      ]
    );
  };

  missingHashes = "${root}/missing-hashes.json";
  offlineCache = yarn-berry.fetchYarnBerryDeps {
    inherit (finalAttrs) src missingHashes;
    hash = "sha256-Qc/kmS/L+Y4e3i1YRlhmQZEtB88JA+t5/5BMQVnZ/UQ=";
  };

  nativeBuildInputs = [
    nodejs
    yarn-berry.yarnBerryConfigHook
    yarn-berry
  ];

  buildPhase = ''
    runHook preBuild
    yarn run ${webpack-environment}:1
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p $out && cp -a assets $out
    runHook postInstall
  '';

  doFixup = false;
})
