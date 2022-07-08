from matplotlib import pyplot

with open('signal.txt') as f:
    lines = f.readlines()

graph_list = []
values = lines[0].split(',')[:-1]
for i in values:
    graph_list.append(float(i))
    
thresh1 = float(lines[1])
thresh1_list = [thresh1 for n in range(len(graph_list))]

thresh2 = float(lines[2])
thresh2_list = [thresh2 for n in range(len(graph_list))]

# save the graph
pyplot.plot(graph_list)
pyplot.plot(thresh1_list)
pyplot.plot(thresh2_list)
graphics_path = 'signal.png'
pyplot.savefig(graphics_path)
print(f"All done! Results saved to {graphics_path}")



