{
  pkgs,
  pyproject-nix,
  uv2nix,
  pyproject-build-systems,
  root,
}:
let
  inherit (pkgs) lib;
  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = root; };
  overlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };
  overrides-sdist = import ./overrides-sdist.nix {
    src = lib.fileset.toSource rec {
      inherit root;
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
in
{
  inherit workspace pythonBase;
}
