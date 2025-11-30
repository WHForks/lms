{
  pkgs,
  pyproject-nix,
  root,
}:
let
  project = pyproject-nix.lib.project.loadPyproject {
    projectRoot = root;
  };
  python = pkgs.python3.override {
    packageOverrides = import ./overrides.nix {
      inherit (pkgs) stdenv fetchFromGitHub;
    };
  };
in
{
  pythonBase = python.withPackages (
    project.renderers.withPackages {
      inherit python;
    }
  );
}
