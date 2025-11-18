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
  inherit
    (import ./nix/mkPython.nix {
      inherit
        pkgs
        pyproject-nix
        uv2nix
        pyproject-build-systems
        ;
      root = ./.;
    })
    workspace
    pythonBase
    ;
  editableOverlay = workspace.mkEditablePyprojectOverlay {
    root = "$REPO_ROOT";
  };
  productionEnv = pythonBase.mkVirtualEnv "lms-prod-env" workspace.deps.default;
  virtualenv = (pythonBase.overrideScope editableOverlay).mkVirtualEnv "lms-env" workspace.deps.all;
in
{
  packages = {
    docker = pkgs.dockerTools.buildLayeredImage {
      name = "lms-docker-image";
      contents = [
        productionEnv
      ];
      config = {
        Cmd = [ "/bin/bash" ];
      };
    };
    frontend = pkgs.callPackage ./nix/frontend.nix {
      root = ./frontend;
    };
  };
  shell = pkgs.mkShell {
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
  };
}
