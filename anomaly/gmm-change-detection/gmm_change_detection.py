import numpy as np
import copy
from preprocess_data import *
from visualization import *
from emd_gmm import *
from gmm import *
import sys
from gmm_mml import GmmMml
import pickle
import os

np.set_printoptions(threshold=sys.maxsize)
np.set_printoptions(suppress = True)

############
# Settings #
############
fake_data = True  # Generate point clouds

# Path to input data (.pk for pickled GMMs, PCL file,
# or bag files cropped to same positions at different times)
t_0 = './data/ground_truth/groundtruth_run5.pcd'
t_1 = './data/ground_truth/groundtruth_run4.pcd'
#t_0 = './saved_models/fake_data_1.pk'
#t_1 = './saved_models/fake_data_2.pk'

# Get file extension
ext = os.path.splitext(os.path.basename(t_0))[1]

#############################
# Set up caching the models #
#############################
def get_filename(original_file):
    '''Make sure the filename is unique'''
    counter = 1
    filename = original_file + "_{}"
    while os.path.isfile('.saved_models/' + filename.format(counter)):
        counter += 1
    filename = filename.format(counter)
    return filename

# Load pre-clustered GMMs if provided
if ext == '.pk':
    with open(t_0, 'rb') as fi:
        gmm1_init_bestk, gmm1_init_bestpp, gmm1_init_bestcov, gmm1_init_bestmu, predictions1 = pickle.load(fi)
    with open(t_1, 'rb') as fi:
        gmm2_init_bestk, gmm2_init_bestpp, gmm2_init_bestcov, gmm2_init_bestmu, predictions2 = pickle.load(fi)
else:
    if fake_data:
        filename_1 = get_filename('fake_data_t0')
        filename_2 = get_filename('fake_data_t1')
    else:
        filename_1 = get_filename(os.path.splitext(os.path.basename(t_0))[0])
        filename_2 = get_filename(os.path.splitext(os.path.basename(t_1))[0])

    t0_save_file = './saved_models/' + filename_1 + '.pk'
    t1_save_file = './saved_models/' + filename_2 + '.pk'

# Select fake data type
appearance = True   # Appearance vs. disappearance of Gaussians

# Visualize GMMs
visualize = True

###################
# Format the data #
###################

if fake_data:
    # Generate 3D data with 4 clusters
    # set Gaussian centers and covariances in 3D
    means = np.array([[1, 0.0, 0.0],
              [0.0, 0.0, 0.0],
                      [-0.5, -0.5, -0.5],
                      [-0.8, 0.3, 0.4]])
    covs = np.array([np.diag([0.01, 0.01, 0.03]),
                     np.diag([0.08, 0.01, 0.01]),
                     np.diag([0.01, 0.05, 0.01]),
                     np.diag([0.03, 0.07, 0.01])])

    N = 1000 #Number of points to be generated for each cluster.
    points_a = []
    points_b = []

    for i in range(len(means)):
        x = np.random.multivariate_normal(means[i], covs[i], N )
        points_a.append(x)
        points_b.append(x)

    points1 = np.concatenate(points_a)

    if appearance:
        # Add an extra Gaussian
        means2 = np.array([[1.5, 1.5, 1.5],
                          [0.2, 0.2, 0.2],
                          [0.8, -.03, -0.4]])
        covs2 = np.array([np.diag([0.01, 0.01, 0.01]),
                         np.diag([0.02, 0.01, 0.03]),
                         np.diag([0.03, 0.02, 0.01])])

        for i in range(len(means2)):
            x = np.random.multivariate_normal(means2[i], covs2[i], N )
            points_b.append(x)

        points2 = np.concatenate(points_b)

    else:
        # Remove an extra Gaussian
        means2 = np.array([[1, 0.0, 0.0],
                          [0.0, 0.0, 0.0],
                          [-0.5, -0.5, -0.5]])
        covs2 = np.array([np.diag([0.01, 0.01, 0.03]),
                         np.diag([0.08, 0.01, 0.01]),
                         np.diag([0.01, 0.05, 0.01])])
        points_b = []

        for i in range(len(means2)):
            x2 = np.random.multivariate_normal(means2[i], covs2[i], N )
            points_b.append(x2)

        points2 = np.concatenate(points_b)

elif ext == '.bag':       # sensor_msgs::PointCloud2 data from bagfile
    points1 = read_pc2_msgs(t_0)
    points2 = read_pc2_msgs(t_1)

elif ext == '.pcd':       # PCL formatted file (e.g. from reconstructed map)
    points1 = read_pcd(t_0)
    points2 = read_pcd(t_1)
else:
    sys.exit('Invalid file format')


# Plot the figures
fig1 = plt.figure()
ax1 = fig1.add_subplot(111, projection='3d')
ax1.scatter(points1[:,0], points1[:,1], points1[:,2], s=0.7, alpha=0.07)
fig2 = plt.figure()
ax2 = fig2.add_subplot(111, projection='3d')
ax2.scatter(points2[:,0], points2[:,1], points2[:,2], s=0.7, alpha=0.07)
#plt.show()

#####################################
# Cluster the point clouds int GMMs #
#####################################

if ext != '.pk':
    # Run split-and-merge expectation-maximization algorithm
    # described in "Unsupervised Learning of Finite Mixture Models" by Figueiredo et al.
    print("Fitting Gamma")
    gmm1_init=GmmMml()
    gmm1_init=gmm1_init.fit(points1, verb=True)

    print("Fitting Theta")
    gmm2_init=GmmMml()
    gmm2_init=gmm2_init.fit(points2, verb=True) 
    gmm1_init_bestk = gmm1_init.bestk
    gmm1_init_bestpp = gmm1_init.bestpp
    gmm1_init_bestcov = gmm1_init.bestcov
    gmm1_init_bestmu = gmm1_init.bestmu
    predictions1 = gmm1_init.predict(points1)

    print("Fitting Theta")
    gmm2_init=GmmMml()
    gmm2_init=gmm2_init.fit(points2, verb=True)
    gmm2_init_bestk = gmm2_init.bestk
    gmm2_init_bestpp = gmm2_init.bestpp
    gmm2_init_bestcov = gmm2_init.bestcov
    gmm2_init_bestmu = gmm2_init.bestmu
    predictions2 = gmm2_init.predict(points2)

 
print("Gamma number of Gaussians: " + str(gmm1_init_bestk))
print("Theta number of Gaussians: " + str(gmm2_init_bestk))

# Move the GMMs to a new data structure to be able to remove
# Gaussians from GMMs for change detection
gamma_t0 = GMM(gmm1_init_bestpp[0,:], gmm1_init_bestmu, gmm1_init_bestcov)
theta_t1 = GMM(gmm2_init_bestpp[0,:], gmm2_init_bestmu, gmm2_init_bestcov)

######################################
# Generate GMM with Detected Changes #
######################################

def find_emd(gmm1, gmm2):
    '''Find the Earth Mover's Distance between two GMMs
    '''
    emdgmm = EMDGMM(gmm1.weights, gmm2.weights)
    emdgmm.get_distance(gmm1.means, gmm2.means)
    emdgmm.calculate_emd()
    return emdgmm.emd

def greedy_select_gmm(gamma, theta, start_emd):
    ''' Find the Gaussian in Theta that contributes the
    highest degree of positive change (i.e., removal results
    in the lowest EMD) and return "best" Theta GMM from which such
    Gaussian has been removed
    '''

    lowest_emd = start_emd # Metric for degree of change 
    best_theta = theta
    best_gauss = GMM(np.array([]), np.array([]).reshape((0,3)), np.array([]).reshape((0,3))) # GMM w/ k=1

    # Remove Gaussians one at a time and track which contributes most change
    for gauss in range(theta.n_gaussians - 1): 
        theta_temp = copy.deepcopy(theta)
        removed_gauss = theta_temp.remove_gaussian(gauss)   # Remove the next Gaussian
        new_emd = find_emd(gamma, theta_temp)
        
        #print("NEW EMD: " + str(new_emd) + " LOWEST: " + str(lowest_emd))

        if new_emd < lowest_emd:
            lowest_emd = new_emd
            best_theta = theta_temp
            best_gauss = removed_gauss

    return lowest_emd, best_theta, best_gauss

def change_detection(gamma, theta):
    '''Greedily remove Gaussians that contribute the most change
    and place them into a tertiary "change" GMM
    '''

    # Initialize empty Pi (change) GMM
    pi = GMM(np.array([]), np.array([]).reshape((0,3)), None)

    # Iteratively remove Gaussians from "after" GMM until EMD is the same
    dGMM_old = find_emd(gamma, theta)
    dGMM, new_theta, best_gauss = greedy_select_gmm(gamma, theta, dGMM_old)

    for i in range(new_theta.n_gaussians):
        # Update Pi with new Gaussian
        pi.add_gaussian(best_gauss)

        # Obtain "best Gaussian" that produces highest degree of change
        dGMM, new_theta, best_gauss = greedy_select_gmm(gamma, new_theta, dGMM_old)
        if dGMM_old > dGMM:
            dGMM_old = dGMM
        else:
            break

    # Output change Gaussian information
    print()
    print("CHANGE GAUSSIANS")
    print("################################")
    print("Number detected: " + str(pi.n_gaussians))
    print("Means: ")
    print(pi.means)
    print("Covariances: ")
    print(pi.covariances)

    # Map the change Gaussians back to the original Theta GMM
    theta_changes = []
    for gauss in range(pi.n_gaussians):
        change_gauss = np.where(np.prod(gmm2_init_bestmu == pi.means[gauss], axis=-1))
        theta_changes.append(change_gauss)

    # Readjust the Pi covariance shape back to [3,3,K]
    pi.covariances = pi.covariances.reshape(pi.n_gaussians,3,3).T
    return pi

pi = change_detection(gamma_t0, theta_t1)

def get_diag(covs, k):
    '''Get diagonal covariance from full covariance
    matrix for plotting'''

    diag_covs = []
    for i in range(k):
        cov = covs[:,:,i]
        l = len(cov[0])
        diag = [cov[j][j] for j in range(l)]
        diag_covs.append(diag)
    return np.array(diag_covs)

########################
# Visualize the Output #
########################
if visualize:
    gmm1_k = gmm1_init_bestk
    gmm2_k = gmm2_init_bestk

    fig = plt.figure(figsize=(9, 3))
    ax1 = fig.add_subplot(131, projection='3d')
    ax1.set(xlabel="X", ylabel="Y", zlabel="Z")
    ax1.title.set_text('Gamma (Before)')

    ax2 = fig.add_subplot(132, projection='3d')
    ax2.set(xlabel="X", ylabel="Y", zlabel="Z")
    ax2.title.set_text('Theta (After)')

    ax3 = fig.add_subplot(133, projection='3d')
    ax3.set(xlabel="X", ylabel="Y", zlabel="Z")
    ax3.title.set_text('Delta (Changes)')

    # GMM 1 (Gamma)
    diag_covs1 = get_diag(gmm1_init_bestcov, gmm1_init_bestk)
    visualize_3d_gmm(points1, predictions1, gmm1_init_bestpp[0], gmm1_init_bestmu.T, np.sqrt(diag_covs1).T, gmm1_k, ax1)

    # GMM 2 (Theta)
    diag_covs2 = get_diag(gmm2_init_bestcov, gmm2_init_bestk)
    visualize_3d_gmm(points2, predictions2, gmm2_init_bestpp[0], gmm2_init_bestmu.T, np.sqrt(diag_covs2).T, gmm2_k, ax2)

    # Change GMM (Pi), compared to GMM2 original points
    piagonal = get_diag(pi.covariances, pi.weights.shape[0])
    visualize_3d_gmm(points2, predictions2, pi.weights, pi.means.T, np.sqrt(piagonal).T, gmm2_k, ax3)

    # Save model parameters for future use
    if ext != ".pk":
        with open(t0_save_file, 'wb') as fi:
            pickle.dump([gmm1_init.bestk, gmm1_init.bestpp, gmm1_init.bestcov, gmm1_init.bestmu, predictions1], fi)
        with open(t1_save_file, 'wb') as fi:
            pickle.dump([gmm2_init.bestk, gmm2_init.bestpp, gmm2_init.bestcov, gmm2_init.bestmu, predictions2], fi)

        print("Saved to: ")
        print("    " + str(t0_save_file))
        print("    " + str(t1_save_file))

plt.show()
