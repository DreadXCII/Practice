"""
Total Weight Calculator
-------------------------
You tell it which plates you're putting on EACH SIDE of the bar,
and it calculates the total weight of the lift (bar + all plates,
both sides).
"""

# Available plates in your gym (in lbs). Edit this list to match what
# you actually have available.
AVAILABLE_PLATES = [45, 35, 25, 10, 5, 2.5]

# Default barbell weight (lbs). Standard Olympic bar is 45 lbs.
DEFAULT_BAR_WEIGHT = 45


def calculate_total(bar_weight, plates_per_side):
    """
    Given a bar weight and a list of plates loaded on ONE side,
    calculate the total weight (bar + plates on both sides).
    """
    return bar_weight + (sum(plates_per_side) * 2)


def format_plate_list(plates):
    if not plates:
        return "(none -- just the bar)"
    return " + ".join(str(p) for p in plates) + " lbs"


def prompt_for_plates(available_plates):
    """
    Lets the user pick plates one at a time from the available list,
    until they're done. Returns the list of plates chosen (per side).
    """
    print("\nAvailable plates:", ", ".join(str(p) for p in available_plates))
    print("Enter plates one at a time (per side). Type 'done' when finished.")

    chosen = []
    while True:
        entry = input(f"Plate #{len(chosen) + 1} (or 'done'): ").strip().lower()

        if entry == "done":
            break

        try:
            plate = float(entry)
        except ValueError:
            print("Please enter a number, or 'done' to finish.")
            continue

        if plate not in available_plates:
            print(
                f"  Note: {plate} lbs isn't in your AVAILABLE_PLATES list, "
                f"but I'll count it anyway."
            )

        chosen.append(plate)

    return chosen


def main():
    print("=" * 50)
    print("TOTAL WEIGHT CALCULATOR")
    print("=" * 50)

    # Get bar weight
    bar_input = input(
        f"Bar weight in lbs [default {DEFAULT_BAR_WEIGHT}]: "
    ).strip()
    bar_weight = float(bar_input) if bar_input else DEFAULT_BAR_WEIGHT

    # Get the plates being loaded on one side
    plates_per_side = prompt_for_plates(AVAILABLE_PLATES)

    total = calculate_total(bar_weight, plates_per_side)

    print("\n" + "-" * 50)
    print(f"Bar weight:      {bar_weight} lbs")
    print(f"Plates per side: {format_plate_list(plates_per_side)}")
    print(f"Weight per side: {sum(plates_per_side)} lbs")
    print(f"TOTAL WEIGHT:    {total} lbs")
    print("-" * 