{ src, ... }:
final: prev:
let
  inherit (final) resolveBuildSystem;
  inherit (builtins) mapAttrs;

  buildSystemOverrides = {
    django-autocomplete-light.setuptools = [ ];
    django-bitfield.setuptools = [ ];
    djangorestframework-camel-case.setuptools = [ ];
  };
  build-system = mapAttrs (
    name: spec:
    prev.${name}.overrideAttrs (old: {
      nativeBuildInputs = old.nativeBuildInputs ++ resolveBuildSystem spec;
    })
  ) buildSystemOverrides;
in
build-system
// {
  hoep = prev.hoep.overrideAttrs (old: {
    env.NIX_CFLAGS_COMPILE = "-Wno-error=incompatible-function-pointer-types";
    nativeBuildInputs = old.nativeBuildInputs ++ [
      (final.resolveBuildSystem {
        setuptools = [ ];
      })
    ];
  });

  lms = prev.lms.overrideAttrs (old: {
    inherit src;
    nativeBuildInputs = old.nativeBuildInputs ++ [
      final.editables
    ];
  });
}
