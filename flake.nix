{
  description = "Bible scripts - diatheke wrapper and format converters";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in {
        bible-scripts = pkgs.stdenv.mkDerivation {
          pname = "bible-scripts";
          version = "unstable";
          src = ./.;
          dontBuild = true;

          nativeBuildInputs = [ pkgs.makeWrapper ];

          # Runtime dependencies (sword moet apart geïnstalleerd zijn)
          propagatedBuildInputs = with pkgs; [
            python3
            pandoc
            fzf
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

            # Wrap Python scripts (diatheke moet in PATH staan via systeem)
            for script in bible-to-format_v2.py bible-format-wrapper.py dutch-diatheke.py; do
              wrapProgram $out/bin/$script \
                --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.python3 pkgs.pandoc ]}
            done

            # Wrap bible script met --inherit-argv0 zodat symlink namen behouden blijven
            wrapProgram $out/bin/bible \
              --inherit-argv0 \
              --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.fzf ]}

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

            # 3) Maak alle symlinks aan + schrijf lijst voor Emacs (gesorteerd)
            mkdir -p $out/share/bible-scripts
            while IFS= read -r link; do
              [[ -n "$link" ]] || continue
              ln -s $out/bin/bible "$out/bin/$link"
              echo "$link" >> $out/share/bible-scripts/commands.txt
            done < <(printf '%s\n' "''${!SYMLINKS[@]}" | ${pkgs.coreutils}/bin/sort)

            runHook postInstall
          '';
        };

        default = self.packages.${system}.bible-scripts;
      });

      # DevShell voor ontwikkeling (sword moet apart geïnstalleerd zijn)
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.mkShell {
            packages = with pkgs; [
              python3
              pandoc
              fzf
            ];
          };
        });
    };
}
