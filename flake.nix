{
  description = "Bible scripts - diatheke wrapper and format converters";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      scriptsDir = ./.;
    in {
      packages.${system} = {
        bible-scripts = pkgs.stdenv.mkDerivation {
          pname = "bible-scripts";
          version = "unstable";
          src = scriptsDir;
          dontBuild = true;
          installPhase = ''
            runHook preInstall

            mkdir -p $out/bin
            cp bible \
              bible-to-format_v2.py \
              bible-format-wrapper.py \
              dutch-diatheke.py \
              bible-symlinks \
              $out/bin/
            patchShebangs $out/bin
            chmod +x $out/bin/bible $out/bin/bible-symlinks

            # Verzamel alle symlinks: uit symlinks.txt + uit repo (merge)
            declare -A SYMLINKS

            # 1) Symlinks uit repo (fallback/basis)
            while IFS= read -r link; do
              [[ -n "$link" ]] || continue
              SYMLINKS["$link"]=1
            done < <(${pkgs.findutils}/bin/find "$src" -maxdepth 1 -type l -lname "bible" -printf "%f\n")

            # 2) Symlinks uit symlinks.txt (override/aanvulling)
            if [[ -f "$src/symlinks.txt" ]]; then
              while IFS= read -r link; do
                [[ -n "$link" ]] || continue
                SYMLINKS["$link"]=1
              done < "$src/symlinks.txt"
            fi

            # 3) Maak alle symlinks aan + schrijf lijst voor Emacs
            mkdir -p $out/share/bible-scripts
            for link in "''${!SYMLINKS[@]}"; do
              ln -s $out/bin/bible "$out/bin/$link"
              echo "$link" >> $out/share/bible-scripts/commands.txt
            done

            runHook postInstall
          '';
        };

        default = self.packages.${system}.bible-scripts;
      };
    };
}
