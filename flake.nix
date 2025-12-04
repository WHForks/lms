{
  outputs =
    { ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forEachSystem =
        f:
        builtins.listToAttrs (
          builtins.map (system: {
            name = system;
            value = f system;
          }) systems
        );
      attrForEachSystem =
        attr: forEachSystem (system: (import ./default.nix { inherit system; })."${attr}");
    in
    {
      checks = attrForEachSystem "checks";
      packages = attrForEachSystem "packages";
    };
}
