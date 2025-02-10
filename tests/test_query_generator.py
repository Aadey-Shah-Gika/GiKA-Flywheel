from flywheel import QueryGenerator


def test_query_generator():
    queries = [
        "This delicious Biscoff Cheesecake recipe features a buttery Biscoff cookie crust, and a creamy Biscoff cheesecake filling. It’s topped with melted Biscoff cookie butter, and Biscoff cookie crumbs, which makes for a stunning and tasty dessert",
        "Mount Everest is the highest mountain in the world. It is located in the Himalayas on the border between Nepal and the Tibet Autonomous Region of China. The mountain's peak reaches an elevation of 8,848 meters (29,029 feet) above sea level.",
        "At its core, a co ord set for women (short for 'coordinated') is a two-piece outfit designed to be worn together, creating a harmonious and, well, coordinated look. These sets can range from casual ensembles perfect for a day out to more formal attire suitable for the office or a night on the town.",
        "Lightweight Gaming Mouse -The Ant Esports GM700 Wireless gaming mouse features a honeycomb shell that weighs only 90 grams, which is light but still durable. The honeycomb shell helps reduce weight to protect your wrist when you are gaming or working.",
        "The Wakeup Mushy Sofa provides a comfortable and supportive seating experience with its plush cushions and sturdy frame | Plush and comfortable: The Wakeup Mushy Sofa provides a luxurious seating experience with its soft and plush cushions, perfect for relaxation and lounging, Soft and supple upholstery for added luxury.",
        "The Mercedes-Benz G-Wagon is a luxury off-road SUV that combines rugged capability with high-end sophistication. Known for its iconic boxy design, powerful engine options, and premium interior, the G-Wagon delivers an unparalleled blend of performance, durability, and prestige. Whether tackling tough terrain or cruising in the city, it offers an elite driving experience with advanced technology and superior craftsmanship.",
        ]
    query_generator = QueryGenerator()
    
    results = [query_generator.generate_queries(query) for query in queries]
    
    for i in range(len(results)):
        print("CONTEXT: \n")
        print(queries[i])
        print("\nQUERIES: \n")
        print('\n'.join(results[i]))
        print('\n=========================================================================================================')
        print('=========================================================================================================\n')
