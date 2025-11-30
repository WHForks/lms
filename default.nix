{
  system ? builtins.currentSystem,
  sources ? import ./npins,
  pkgs ? import sources.nixpkgs { inherit system; },
  lib ? pkgs.lib,
  pyproject-nix ? import sources.pyproject-nix { inherit lib; },

}:
let
  project = pyproject-nix.lib.project.loadPyproject {
    projectRoot = ./.;
  };
  python = pkgs.python3.override {
    packageOverrides = import ./nix/overrides.nix {
      inherit (pkgs) stdenv fetchFromGitHub;
    };
  };
  pythonBase = python.withPackages (
    project.renderers.withPackages {
      inherit python;
    }
  );
  virtualenv = pythonBase;
in
{
  packages = {
    docker = pkgs.dockerTools.buildLayeredImage {
      name = "lms-docker-image";
      contents = [
        virtualenv
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
