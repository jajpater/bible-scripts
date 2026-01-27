{
  description = "Bible scripts - diatheke wrapper and format converters";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      # SWORD met DutSVV versification patch
      sword-patched = pkgs.sword.overrideAttrs (old: {
        postPatch = (old.postPatch or "") + ''
          echo "Applying DutSVV versification patch..."
          patch -p0 < ${./dutsvv-versification.patch}
        '';
      });
    in {
      packages.${system} = {
        bible-scripts = pkgs.stdenv.mkDerivation {
          pname = "bible-scripts";
          version = "unstable";
          src = ./.;
          dontBuild = true;

          nativeBuildInputs = [ pkgs.makeWrapper ];

          # Runtime dependencies - beschikbaar voor de scripts
          propagatedBuildInputs = [
            pkgs.python3
            pkgs.pandoc
            pkgs.fzf
            sword-patched
          ];

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

            # Wrap Python scripts zodat ze python3 en dependencies kunnen vinden
            for script in bible-to-format_v2.py bible-format-wrapper.py dutch-diatheke.py; do
              wrapProgram $out/bin/$script \
                --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.python3 pkgs.pandoc sword-patched ]}
            done

            # Wrap bible script voor fzf en diatheke (sword)
            wrapProgram $out/bin/bible \
              --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.fzf sword-patched ]}

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

      devShells.${system}.default = pkgs.mkShell {
        packages = [
          pkgs.python3
          pkgs.pandoc
          pkgs.fzf
          sword-patched
        ];
      };
    };
}
