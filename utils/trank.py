#!/usr/bin/env python3

import argparse

MARKET_FACTOR = 1.44
SG_BASE = 10
SG_STEP = 0.15


def calculate_price(material_cost: float, sg: int) -> float:
    sg_factor = 1 + (sg - SG_BASE) * SG_STEP
    return material_cost * sg_factor * MARKET_FACTOR


def main():
    parser = argparse.ArgumentParser(
        description="Berechnet den Preis eines Zaubertranks (DnD)"
    )

    parser.add_argument(
        "material", type=float, help="Materialkosten in Gold (z. B. 34.65)"
    )

    parser.add_argument("sg", type=int, help="Schwierigkeit (SG), Heiltrank = 10")

    args = parser.parse_args()

    price = calculate_price(args.material, args.sg)

    print("\n🧪 Trankpreis-Berechnung")
    print("-----------------------")
    print(f"Materialkosten: {args.material:.2f} g")
    print(f"SG:             {args.sg}")
    print(f"Endpreis:       {round(price)} g")
    print(f"(exakt:         {price:.2f} g)\n")


if __name__ == "__main__":
    main()
