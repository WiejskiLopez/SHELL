przejdziemy na nowoczesny typer

2. **Czy CLI ma być nadal `typer`/argparse, czy reuse argparse identyczne jak teraz?** Rekomendacja: argparse 1:1 dla zachowania kompatybilności argv (zero ryzyka regresji wywołań subprocess między node'ami).