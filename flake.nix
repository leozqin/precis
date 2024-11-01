{
  description = "A Nix-flake-based dev env for Precis";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05";
  };

  outputs = { self , nixpkgs ,... }: let
    # system should match the system you are running on
    system = "x86_64-linux";
  in {
    devShells."${system}".default = let
      pkgs = import nixpkgs {
        inherit system;
      };
    in pkgs.mkShell {
      name = "precis";
      # create an environment with nodejs_18, pnpm, and yarn
      packages = with pkgs; [
        python311Full
        python311Packages.pip
        nodejs_22
        pre-commit
        gnumake
        playwright
        ungoogled-chromium
        go_1_21
      ];

      shellHook = ''
        python -m venv .venv
        source .venv/bin/activate
      '';
    };
  };
}
