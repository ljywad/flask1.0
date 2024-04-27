# data_processing.py

import numpy as np
from scipy.linalg import svd

def svd_denoise(data_matrix, k=5):
    U, s, Vt = svd(data_matrix, full_matrices=False)
    denoised_matrix = np.dot(U[:, :k], np.dot(np.diag(s[:k]), Vt[:k, :]))
    return denoised_matrix
