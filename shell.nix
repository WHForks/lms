{
  system ? builtins.currentSystem,
  sources ? import ./npins,
  pkgs ? import sources.nixpkgs { inherit system; },
  lib ? pkgs.lib,
  pyproject-nix ? import sources.pyproject-nix { inherit lib; },
  uv2nix ? import sources.uv2nix { inherit lib pyproject-nix; },
  pyproject-build-systems ? import sources.build-system-pkgs {
    inherit uv2nix pyproject-nix lib;
  },
}:
let
  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
  overlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };
  editableOverlay = workspace.mkEditablePyprojectOverlay {
    root = "$REPO_ROOT";
  };
  overrides-sdist = import ./nix/overrides-sdist.nix {
    src = lib.fileset.toSource rec {
      root = ./.;
      fileset = lib.fileset.unions (
        map (path: root + path) [
          "/pyproject.toml"
          "/lms/"
          "/conftest.py"
          "/manage.py"
          "/pytest.ini"
          "/README.md"
        ]
      );
    };
  };
  overlays = lib.composeManyExtensions [
    pyproject-build-systems.wheel
    overlay
    overrides-sdist
  ];
  python = pkgs.python310;
  pythonBase =
    (pkgs.callPackage pyproject-nix.build.packages {
      inherit python;
    }).overrideScope
      overlays;
  virtualenv = (pythonBase.overrideScope editableOverlay).mkVirtualEnv "lms-env" workspace.deps.all;
in
pkgs.mkShell {
  packages = [
    virtualenv
    pkgs.uv

    pkgs.nodejs_20
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
  };
  shellHook = ''
    unset PYTHONPATH
    export REPO_ROOT=$(git rev-parse --show-toplevel)
  '';
}
