from Island import Island ,Animal
royale = Island(10)
print(royale)

animal1 = Animal(Island=royale, x=4, y=8, s="A")
royale.register(animal1)

animal2 = Animal(Island=royale, x=6, y=4, s="B")
royale.register(animal2)

print(royale)