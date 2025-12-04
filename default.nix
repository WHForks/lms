{
  system ? builtins.currentSystem,
  sources ? import ./npins,
  pkgs ? import sources.nixpkgs { inherit system; },
  lib ? pkgs.lib,
  pyproject-nix ? import sources.pyproject-nix { inherit lib; },
}:
let
  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions (
      map (path: ./. + path) [
        "/pyproject.toml"
        "/lms/"
        "/conftest.py"
        "/manage.py"
        "/pytest.ini"
        "/README.md"
        "/locale"
      ]
    );
  };
  project = pyproject-nix.lib.project.loadPyproject {
    projectRoot = ./.;
  };
  packageOverrides = import ./nix/overrides.nix {
    inherit (pkgs) fetchFromGitHub;
  };
  python = pkgs.python312.override {
    inherit packageOverrides;
  };
  pythonBase = python.withPackages (
    project.renderers.withPackages {
      inherit python;
      groups = [ "dev" ];
    }
  );
  productionEnv = python.withPackages (project.renderers.withPackages { inherit python; });
  frontendAssets = pkgs.callPackage ./nix/frontend.nix {
    root = ./frontend;
  };
  compiledMessages = pkgs.callPackage ./nix/compiled-messages.nix {
    inherit src;
    pythonEnv = productionEnv;
  };
  staticAssets = pkgs.callPackage ./nix/static-assets.nix {
    inherit src frontendAssets compiledMessages;
    pythonEnv = productionEnv;
  };
  databaseWithMigrations = pkgs.callPackage ./nix/migrate.nix {
    inherit src;
    pythonEnv = productionEnv;
  };
in
{
  packages = {
    inherit
      frontendAssets
      compiledMessages
      staticAssets
      databaseWithMigrations
      ;
    docker = pkgs.callPackage ./nix/docker.nix {
      inherit
        src
        productionEnv
        frontendAssets
        staticAssets
        ;
    };
  };

  checks = {
    pytest = pkgs.callPackage ./nix/pytest.nix {
      inherit src databaseWithMigrations;
      pythonEnv = pythonBase;
    };
  };

  shell = pkgs.mkShell {
    packages = [
      pythonBase
      pkgs.uv

      pkgs.nodejs
      pkgs.yarn-berry

      pkgs.ruff
      pkgs.nixfmt-tree

      pkgs.process-compose
      pkgs.docker-client
    ];

    env = {
      UV_NO_SYNC = "1";
      UV_PYTHON = pythonBase.python.interpreter;
      UV_PYTHON_DOWNLOADS = "never";
      PYTHONPATH = toString ./lms/apps;
    };
  };
}
