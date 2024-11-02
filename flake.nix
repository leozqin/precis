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
        playwright-driver.browsers
        go_1_21
      ];

      PLAYWRIGHT_NODEJS_PATH = "${pkgs.nodejs_22}/bin/node";
      PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright-driver.browsers}";
      PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = 1;
    };
  };
}
