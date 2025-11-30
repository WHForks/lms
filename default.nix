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
      inherit (pkgs) fetchFromGitHub;
    };
  };
  pythonBase = python.withPackages (
    project.renderers.withPackages {
      inherit python;
      groups = [ "dev" ];
    }
  );
  virtualenv = pythonBase;
in
{
  packages = {
    docker = pkgs.dockerTools.buildLayeredImage {
      name = "lms-docker-image";
      contents = [
        (python.withPackages (project.renderers.withPackages { inherit python; }))
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
      PYTHONPATH = toString ./lms/apps;
    };
    shellHook = ''
      ln -snf ${pythonBase} .python-env
    '';
  };
}
