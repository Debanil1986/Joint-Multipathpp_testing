import numpy as np
import matplotlib.pyplot as plt


data = np.load('/workspaces/Joint-Multipathpp_testing/prerendered/data/scid_1a8cb387968480a1.npz')
# Access individual arrays
for item in data.files:
    print("ITEM--->",item)
    print("Data ---> ",data[item])
    


# Load the npz file
# data = np.load('/workspaces/Joint-Multipathpp_testing/prerendered/data/scid_1a8cb387968480a1.npz')

# # For 2D array/image visualization
plt.imshow(data['road_network_embeddings'])
plt.colorbar()
plt.show()
