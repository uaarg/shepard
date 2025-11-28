import numpy as np

"""

This file provides methods to perform computations that apply to imaging functions

"""

def skew(x):
    """
    Returns a skew-symmetric matrix of a 3-vector.

    For example: (1, 2, 3) becomes [0, -3, 2]
                                   [3,  0, -1]
                                   [-2, 1, 0]
    """
    return np.array([
        [0, -x[2], x[1]],
        [x[2], 0, -x[0]],
        [-x[1], x[0], 0]
    ], dtype=float)


def dlt(x, X, w=None):
    """
    Performs a Direct Linear Transform (DLT) to estimate a camera projection matrix P

    See 4.2 in Computer Vision: Three-Dimensional Reconstruction Techniques (https://search.library.ualberta.ca/discovery/fulldisplay?context=L&vid=01UOA_INST:UOA&search_scope=MyInst_and_CI&tab=Everything&docid=alma991043592432009116)

    Parameters:
        x : (2, N) image points (pixel coordinates) 
        X : (3, N) real points (real world coordinates x, y, z)
        w : weights (optional)

    Returns: 
        P : (3, 4) projection matrix
    """

    N = X.shape[1]

    if w is None:
        w = np.ones(N)
    
    # Convert coordinates to homogenous coordinates
    X_h = np.vstack([X, np.ones(N)])
    x_h = np.vstack([x, np.ones(N)]) 

    L = []

    for i in range(N):
        X_i = X_h[:, i]
        x_i = x_h[:, i]

        # Compute the Kronecker product: kron(X_i^T, skew(x_i))

        block = w[i] * np.kron(X_i.reshape(1, -1), skew(x_i))
        L.append(block)

    L = np.vstack(L)

    # Solve L p = 0 using Singular Value Decomposition (SVD)

    _, _, Vt = np.linalg.svd(L)
    p = Vt[-1]

    # Reshape into the 3x4 Projection Matrix P
    P = p.reshape(3, 4)

    return P
