nomes = []
notas1 = []
notas2 = []

for i in range(5):
    print(f"\nAluno {i+1}:")
    nome = input("Nome: ")
    n1 = float(input("Nota N1: "))
    n2 = float(input("Nota N2: "))

    nomes.append(nome)
    notas1.append(n1)
    notas2.append(n2)

print("\n Lista de Alunos e Notas ")
for i in range(5):
    print(f"{nomes[i]} - N1: {notas1[i]}, N2: {notas2[i]}")