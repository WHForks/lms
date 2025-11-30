{ stdenv, fetchFromGitHub, ... }:
self: super: {
  django-bitfield = self.buildPythonPackage rec {
    pname = "django-bitfield";
    version = "2.2.0";
    pyproject = true;

    build-system = [ self.setuptools ];
    dependencies = with self; [
      django
      six
    ];

    src = self.fetchPypi {
      inherit pname version;
      hash = "sha256-GyEmKsxOwK8/gu0ESYoFbNnVRSUyrAJ3HgBINaNOCxs=";
    };
  };

  django-choices = self.buildPythonPackage rec {
    pname = "django-choices";
    version = "1.7.2";
    pyproject = true;

    build-system = [ self.setuptools ];
    dependencies = with self; [
      django
      six
    ];

    src = self.fetchPypi {
      inherit pname version;
      hash = "sha256-5S8dn+Ov2SYRvS6jE62Ka6Kon9sS1eUYQ4iStq5GLuM=";
    };
  };

  django-loginas = self.buildPythonPackage rec {
    pname = "django-loginas";
    version = "0.3.13";
    pyproject = true;

    build-system = [ self.setuptools ];

    src = fetchFromGitHub {
      owner = "skorokithakis";
      repo = "django-loginas";
      tag = "v${version}";
      hash = "sha256-tn/PKL7ZbDPrKDA0oJ8TuppqSOKHFxKuggQJNqPX+Z8=";
    };
  };

  django-recaptcha = self.buildPythonPackage rec {
    pname = "django-recaptcha";
    version = "4.0.0";
    pyproject = true;

    build-system = [ self.setuptools ];
    dependencies = with self; [ django ];

    src = self.fetchPypi {
      inherit pname version;
      hash = "sha256-UxZDj5dwDEMdZTUUcNElUEfj8s2a8PLxNZK2N9rZIT4=";
    };
  };

  django-registration-redux = self.buildPythonPackage rec {
    pname = "django-registration-redux";
    version = "2.13";
    pyproject = true;

    build-system = [ self.setuptools ];

    src = self.fetchPypi {
      inherit pname version;
      hash = "sha256-l5OgWzKx1zQsbvPgFAspUbfb3gWLO6boojK1NJKCefk=";
    };
  };

  django-ses = self.buildPythonPackage rec {
    pname = "django-ses";
    version = "4.1.1";
    pyproject = true;

    build-system = [ self.poetry-core ];
    dependencies = with self; [
      boto3
      django
    ];

    src = fetchFromGitHub {
      owner = "django-ses";
      repo = "django-ses";
      tag = "v${version}";
      hash = "sha256-kRle+nLUgxqEE/Lv+VPs0PjPV/LbLBrl++1ca2Bn/5s=";
    };
  };

  django-simple-menu = self.buildPythonPackage rec {
    pname = "django-simple-menu";
    version = "2.1.4";
    pyproject = true;

    build-system = [ self.setuptools ];
    nativeBuildInputs = [ self.setuptools-scm ];
    dependencies = with self; [ django ];

    src = fetchFromGitHub {
      owner = "jazzband";
      repo = "django-simple-menu";
      tag = "v${version}";
      hash = "sha256-XNPEFsGYAGj0ZMxX+i4Z72C0bHUvZ4HTmcRO06emdZw=";
    };
  };

  django-vanilla-views = self.buildPythonPackage rec {
    pname = "django-vanilla-views";
    version = "3.0.0";
    pyproject = true;

    build-system = [ self.setuptools ];

    src = self.fetchPypi {
      inherit pname version;
      hash = "sha256-tl8nuNXeU/aVo5dDgze+iCpse12NMDM6TPmMkjn+C4Y=";
    };
  };

  hoep = self.buildPythonPackage {
    pname = "hoep";
    version = "2.0.2";
    pyproject = true;

    build-system = [ super.setuptools ];

    src = fetchFromGitHub {
      owner = "pacahon";
      repo = "Hoep";
      rev = "0d4c0507dcb34d1b63a099c8b08656b66394bc37";
      hash = "sha256-oYgtdD4jvV+Lq+6tOz/9s/8m9Qn+eKggI/0mqDZxXrA=";
      fetchSubmodules = true;
    };

    env.NIX_CFLAGS_COMPILE = "-Wno-error=${
      if stdenv.cc.isClang then "incompatible-function-pointer-types" else "incompatible-pointer-types"
    }";
  };

  rest-pandas = self.buildPythonPackage rec {
    pname = "rest-pandas";
    version = "1.1.0";
    pyproject = true;

    build-system = [ self.setuptools ];
    nativeBuildInputs = [ self.setuptools-scm ];
    dependencies = with self; [
      djangorestframework
      pandas
    ];

    src = self.fetchPypi {
      inherit pname version;
      hash = "sha256-E3ljmFZaCMZo4P0xhhk5320PnMhZsUkzCPfMXBHqJHw=";
    };
  };

  social-auth-app-django = super.social-auth-app-django.overrideAttrs (
    finalAttrs: oldAttrs: {
      version = "5.4.3";

      src = fetchFromGitHub {
        owner = "python-social-auth";
        repo = "social-app-django";
        tag = finalAttrs.version;
        hash = "sha256-gejt/DBJ6tw/GKK84YjfY1OpYkcCjEAsWLYsID3qqDM=";
      };

      meta = oldAttrs.meta // {
        broken = false;
      };
    }
  );
}
