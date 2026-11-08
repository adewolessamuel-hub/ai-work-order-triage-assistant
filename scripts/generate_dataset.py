import csv, random, collections, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else "data/work_orders_regenerated.csv"
from datetime import datetime, timedelta

random.seed(42)

P = {
    "E1": ("Maple Hollow Estate", "Residential"),
    "E2": ("Brookside Village", "Residential"),
    "O":  ("Lakeshore Corporate Centre", "Office"),
}

# (trade, property, location, requester_role, text)
R = [
# ---------------- Plumbing ----------------
("Plumbing","E1","Unit 14, Block C","Resident","Water is coming through my ceiling from the unit above. Dripping fast into a bucket and the light fixture is filling with water. Please come NOW."),
("Plumbing","E2","27 Willow Crescent","Resident","Kitchen tap drips constantly, been like this about two weeks. Not urgent but annoying at night."),
("Plumbing","O","Floor 4, women's washroom","Tenant admin","Two of the four toilets are not flushing. Staff are going down to the 3rd floor and queueing."),
("Plumbing","E1","Unit 3, Block A","Resident","No hot water since this morning. I have a toddler at home."),
("Plumbing","E2","9 Birchwood Lane","Resident","Basement floor drain is gurgling and there is a bad sewage smell after the neighbour ran laundry."),
("Plumbing","O","Floor 1, kitchenette","Tenant","Kitchenette sink is draining slowly. Probably coffee grounds."),
("Plumbing","E1","Unit 22, Block D","Resident","Shower head is loose and spraying sideways. Pressure is also low."),
("Plumbing","E2","41 Cedar Court","Resident","Outdoor tap leaks at the base whenever a hose is connected."),
("Plumbing","O","Basement 1, mechanical room","Security guard","Found a puddle about 2 m wide around the domestic hot water tank. Tank is making a knocking noise."),
("Plumbing","E1","Unit 8, Block B","Resident","Toilet runs on and off all night. Water bill went up last month."),
# ---------------- HVAC ----------------
("HVAC","O","Floor 7, server room","Tenant IT lead","Server room AC alarm shows 31C with the door closed. Our equipment will start shutting down soon."),
("HVAC","E1","Unit 19, Block C","Resident","Furnace will not start. Thermostat says heat is on but only cold air comes out. It is 2 degrees outside and my elderly mother lives with me."),
("HVAC","E2","15 Poplar Drive","Resident","I think the furnace filter has not been changed in over a year. Can someone swap it?"),
("HVAC","O","Floor 3, east open area","Tenant","East side is freezing, people are wearing coats. Been like this since Monday."),
("HVAC","E1","Unit 6, Block A","Resident","Faint rotten egg smell near the furnace closet. Comes and goes."),
("HVAC","E2","52 Maple Grove","Resident","Outdoor AC unit is making a loud rattling noise when it runs."),
("HVAC","O","Floor 5, Suite 520","Tenant","Thermostat screen is blank and we can't adjust the temperature."),
("HVAC","E1","Unit 11, Block B","Resident","Bathroom exhaust fan makes a grinding sound and doesn't pull steam out."),
("HVAC","E2","8 Hawthorn Way","Resident","Heat only works on the main floor. Upstairs bedrooms are cold."),
("HVAC","O","Roof, RTU-3","Building operator","Rooftop unit 3 belt is squealing loudly. Tenants on floor 9 are complaining about noise."),
# ---------------- Electrical ----------------
("Electrical","E2","33 Oakridge Avenue","Resident","Burning smell from the living room outlet. The outlet is warm and has gone brown around the edges."),
("Electrical","O","Floor 2, corridor near Stairwell B","Property coordinator","Three light fixtures are out in the corridor beside the stairwell. It is dark at night."),
("Electrical","E1","Unit 17, Block C","Resident","Breaker keeps tripping when the microwave and kettle run together."),
("Electrical","O","Parking level P2","Security guard","About half of the lights on P2 are out. Evening staff don't feel safe walking to their cars."),
("Electrical","E1","Unit 5, Block A","Resident","Doorbell does not work."),
("Electrical","E2","19 Elm Street","Resident","I heard sparking when I pressed the garage door opener and now the garage has no power."),
("Electrical","O","Floor 3, Suite 305","Tenant","We need 4 extra outlets for new workstations. Move-in is Dec 1."),
("Electrical","E1","Block D lobby","Resident","Pot lights in the lobby are flickering and a few are buzzing."),
("Electrical","E2","6 Spruce Lane","Resident","No power at the kitchen outlets only. Rest of the house is fine. I checked the breaker panel."),
("Electrical","O","Floor 6, elevator lobby","Cleaner","Outlet cover is cracked and the wires are visible behind it."),
# ---------------- Carpentry ----------------
("Carpentry","E1","Unit 2, Block A","Resident","Front door doesn't latch properly. I have to lift the handle to lock it."),
("Carpentry","E2","24 Pine Ridge","Resident","Kitchen cabinet door fell off its hinge."),
("Carpentry","O","Floor 6, boardroom","Tenant admin","Boardroom table leg is loose and the table wobbles. Client meeting on Thursday."),
("Carpentry","E1","Unit 13, Block C balcony","Resident","Balcony railing wobbles when leaned on. One post feels loose at the base."),
("Carpentry","E2","38 Aspen Court","Resident","Third and fifth stair steps squeak loudly."),
("Carpentry","O","Floor 1, reception","Receptionist","Laminate is peeling at the edge of the reception desk."),
("Carpentry","E1","Unit 9, Block B","Resident","Closet sliding door came off its track."),
("Carpentry","E2","12 Juniper Road","Resident","A back deck board broke and my son's foot went through it. He's okay, just scraped. Other boards look soft too."),
("Carpentry","O","Floor 2, Suite 215","Tenant","Please install a 3 m wall-mounted shelving unit in our storage room. We will supply the unit."),
("Carpentry","E1","Block D, 2nd floor stairs","Resident","Stair handrail has pulled away from the wall a bit."),
# ---------------- Painting & Drywall ----------------
("Painting & Drywall","E2","29 Willow Crescent","Resident","Fist-sized hole in the hallway drywall from a door handle."),
("Painting & Drywall","O","Floor 8, corridor","Cleaner","Water stain is spreading on a ceiling tile near the washroom."),
("Painting & Drywall","E1","Unit 20, Block D","Property manager","Whole unit needs repainting before the new tenant moves in on the 15th."),
("Painting & Drywall","E2","4 Cherry Lane","Resident","Paint is peeling on the bathroom ceiling above the shower and there are black spots."),
("Painting & Drywall","O","Floor 1, Suite 120","Tenant","Scuff marks on walls after a furniture move. Touch up whenever convenient."),
("Painting & Drywall","E1","Unit 7, Block A","Resident","Bedroom ceiling has a crack about a metre long and bits of plaster are falling."),
("Painting & Drywall","O","Stairwell A, floor 4","Security guard","Marker graffiti on the stairwell wall."),
("Painting & Drywall","E2","47 Beech Street","Resident","Multiple nail pops in the living room ceiling drywall."),
("Painting & Drywall","E1","Block C, 3rd floor corridor","Resident","Paint is chipped beside the elevator."),
("Painting & Drywall","O","Floor 4, pantry","Tenant","Dark patches on the wall behind the pantry fridge. Might be mould."),
# ---------------- Roofing & Envelope ----------------
("Roofing & Envelope","E2","14 Hawthorn Way","Resident","Water stain on the top floor bedroom ceiling after yesterday's rain. It is getting bigger."),
("Roofing & Envelope","E1","Block B roof","Groundskeeper","Several shingles blew off last night. Found them in the courtyard."),
("Roofing & Envelope","O","Floor 9, Suite 900","Tenant","Window seal has failed on 3 windows. Condensation between the panes."),
("Roofing & Envelope","E2","22 Elm Street","Resident","Eavestrough overflows at the front corner and pours onto the walkway."),
("Roofing & Envelope","E1","Unit 15, Block C","Resident","Cold draft around the balcony door."),
("Roofing & Envelope","O","Roof, near access hatch","Building operator","Standing water on the roof near the hatch. Drain looks blocked."),
("Roofing & Envelope","E2","36 Poplar Drive","Resident","A siding panel is cracked beside the garage."),
("Roofing & Envelope","E1","Unit 1, Block A","Resident","Water comes in around the window frame during heavy rain and soaks the carpet."),
("Roofing & Envelope","O","Loading dock","Dock supervisor","Weatherstripping on the loading dock door is torn and wind blows in."),
("Roofing & Envelope","E2","3 Birch Lane","Resident","Gap in the soffit near the roof edge. Birds are going in and out."),
# ---------------- Landscaping & Grounds ----------------
("Landscaping & Grounds","E1","Visitor parking","Groundskeeper","Large tree branch fell across the visitor parking and blocks four spots."),
("Landscaping & Grounds","E2","17 Willow Crescent","Resident","Lawn hasn't been cut in three weeks."),
("Landscaping & Grounds","O","Front plaza","Receptionist","Paving stone is lifted at the main entrance. A visitor almost fell today."),
("Landscaping & Grounds","E1","Courtyard walkways","Resident","Wet leaves are clogging the walkways and they are very slippery."),
("Landscaping & Grounds","E2","Brookside playground","Resident","Chain on one of the swings is broken."),
("Landscaping & Grounds","O","Visitor entrance, parking lot","Tenant","Pothole about 30 cm wide near the visitor entrance."),
("Landscaping & Grounds","E1","Block A garden","Resident","Sprinkler comes on at 2 am and floods the path."),
("Landscaping & Grounds","E2","55 Cherry Lane","Resident","Neighbour's tree branches are touching my roof."),
("Landscaping & Grounds","O","Main entrance planters","Property coordinator","Planters are dead. Please replace for fall."),
("Landscaping & Grounds","E1","East boundary","Resident","A fence panel fell down along the east boundary after the wind."),
# ---------------- Pest Control ----------------
("Pest Control","E1","Unit 16, Block C","Resident","Seeing cockroaches in the kitchen at night. Several. Neighbour says they have them too."),
("Pest Control","O","Floor 3, kitchenette","Tenant","Found mouse droppings in the kitchenette cupboards."),
("Pest Control","E2","31 Aspen Court","Resident","Wasp nest under the front porch roof. Kids play there."),
("Pest Control","E1","Unit 4, Block A","Resident","Waking up with bites on my arms and I found small dark spots along the mattress seam."),
("Pest Control","E2","10 Spruce Lane","Resident","Ants in the kitchen every morning, trailing in from the window."),
("Pest Control","O","Loading dock","Dock supervisor","Rats seen near the garbage bins at the loading dock."),
("Pest Control","E1","Block D garbage room","Resident","Garbage room smells and there are flies everywhere."),
("Pest Control","E2","44 Beech Street","Resident","Scratching noises in the attic at night. Might be a raccoon."),
("Pest Control","O","Floor 10, Suite 1005","Tenant","A few fruit flies around our office plants."),
("Pest Control","E1","Unit 12, Block B","Resident","Heard mice in the walls last week and caught one in the pantry."),
# ---------------- Fire & Life Safety ----------------
("Fire & Life Safety","O","Floor 5","Property coordinator","Fire alarm panel has shown a trouble light for two days."),
("Fire & Life Safety","E1","Unit 21, Block D","Resident","Smoke detector chirps every minute. Probably the battery."),
("Fire & Life Safety","E2","18 Oakridge Avenue","Resident","CO detector went off briefly this morning near the furnace. It stopped on its own."),
("Fire & Life Safety","O","East stairwell, ground floor","Security guard","Exit sign above the east stairwell door is not lit."),
("Fire & Life Safety","E1","Block B corridor","Resident","Fire extinguisher is missing from its cabinet in the corridor."),
("Fire & Life Safety","O","Floor 2, stairwell door","Security guard","Stairwell fire door is propped open with a wedge. Smokers are doing it."),
("Fire & Life Safety","E1","Unit 10, Block B","Resident","Hallway smoke alarm was removed during painting last week and never put back."),
("Fire & Life Safety","E2","25 Pine Ridge","Resident","Fire extinguisher tag shows it expired in 2023."),
("Fire & Life Safety","O","Floor 6, room beside server closet","Tenant","Sprinkler head is dripping slightly. One drip every few seconds."),
("Fire & Life Safety","E1","Block C","Resident","Fire alarm sounded at 3 am. Residents silenced it, no fire seen. Panel says zone 4."),
# ---------------- Locksmith & Access Control ----------------
("Locksmith & Access Control","E2","7 Hawthorn Way","Resident","Locked out with my keys inside. It's 9 pm and I have a baby."),
("Locksmith & Access Control","O","Main entrance","Receptionist","Badge reader at the main entrance isn't reading cards. People are propping the door open."),
("Locksmith & Access Control","E1","Unit 18, Block C","Resident","Lost my fob for the building door. Please deactivate it and issue a new one."),
("Locksmith & Access Control","O","Floor 6, Suite 610","Tenant","Need the suite re-keyed after an employee left."),
("Locksmith & Access Control","E2","20 Birch Lane","Resident","Key broke off in the mailbox lock."),
("Locksmith & Access Control","E1","Block A main door","Resident","Door doesn't close fully so anyone can walk in. The magnetic lock isn't holding."),
("Locksmith & Access Control","O","Floor 1, telecom closet","Tenant","Lock on the telecom closet is jammed. Our ISP technician can't get in. Appointment is tomorrow at 9 am."),
("Locksmith & Access Control","E2","Visitor gate","Resident","Keypad code for the visitor gate isn't working for my guests."),
("Locksmith & Access Control","E1","Unit 9, Block B","Resident","Deadbolt is stiff and hard to turn, but it still works."),
("Locksmith & Access Control","O","Parking gate","Security guard","Parking gate arm is stuck in the up position. It won't close overnight."),
]

assert len(R) == 100, len(R)

channels = ["Resident portal", "Phone", "Email", "Walk-in", "Tenant portal"]
def channel(prop):
    if prop == "O":
        return random.choice(["Tenant portal", "Email", "Phone", "Walk-in"])
    return random.choice(["Resident portal", "Phone", "Email", "Walk-in"])

start = datetime(2026, 10, 5, 7, 0)
rows = []
for trade, prop, loc, role, text in R:
    t = start + timedelta(days=random.randint(0, 27), minutes=random.randint(0, 14 * 60))
    # late-night/early-morning timestamps for a few requests that say so
    low = text.lower()
    if "3 am" in low: t = t.replace(hour=3, minute=random.randint(5, 40))
    if "9 pm" in low: t = t.replace(hour=21, minute=random.randint(5, 40))
    if "2 am" in low: t = t.replace(hour=random.choice([7, 8]))
    rows.append((t, trade, prop, loc, role, text))

rows.sort(key=lambda r: r[0])
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["request_id", "submitted_at", "property", "property_type", "location", "trade", "requester_role", "channel", "request_text"])
    for i, (t, trade, prop, loc, role, text) in enumerate(rows, 1):
        name, ptype = P[prop]
        w.writerow([f"WO-{i:03d}", t.strftime("%Y-%m-%d %H:%M"), name, ptype, loc, trade, role, channel(prop), text])

c = collections.Counter(r[2] for r in rows)
print({P[k][0]: v for k, v in c.items()})
print(collections.Counter(r[1] for r in rows))
