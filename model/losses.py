import torch
from torch import nn
import numpy as np
from torch.distributions.lowrank_multivariate_normal import LowRankMultivariateNormal


def ade_loss(gt, predictions, confidences, avails, covariance_matrices):
    """
    Compute ade loss.
    Args:
        gt.shape is [b, n, t, 2]
        predictions.shape is [b, n, m, t, 2]
        confidences.shape is [b, n, m]
        avails.shape is [b, n, t, 1]
        covariance_matrices,shape is [b, n, m, t, 2, 2]
    Returns:
        a single float number
    """
    gt = torch.unsqueeze(gt, 2)
    avails = avails[:, :, None, :, :]
    error = (gt - predictions) * (gt - predictions)
    error = error * avails
    error = torch.mean(error, axis=[-1, -2])
    error, _ = torch.min(error, axis=-1)
    assert torch.isfinite(error).all()
    return torch.mean(error)


def nll_with_covariances(gt, predictions, confidences, avails, covariance_matrices):
    """
    Compute nll loss.
    Args:
        gt.shape is [b, n, t, 2]
        predictions.shape is [b, n, m, t, 2]
        confidences.shape is [b, n, m]
        avails.shape is [b, n, t, 1]
        covariance_matrices,shape is [b, n, m, t, 2, 2]
    Returns:
        a single float number
    """
    precision_matrices = torch.inverse(covariance_matrices)
    gt = torch.unsqueeze(gt, 2)
    avails = avails[:, :, None, :, :]
    coordinates_delta = (gt - predictions).unsqueeze(-1)
    errors = coordinates_delta.permute(0, 1, 2, 3, 5, 4) @ precision_matrices @ coordinates_delta
    assert torch.isfinite(errors).all()
    # print(torch.max(covariance_matrices), torch.min(covariance_matrices))
    errors = avails * (-0.5 * errors.squeeze(-1) - 0.5 * torch.logdet(covariance_matrices).unsqueeze(-1))
    assert torch.isfinite(errors).all()
    with np.errstate(divide="ignore"):
        errors = nn.functional.log_softmax(confidences, dim=2) + \
            torch.sum(errors, dim=[3, 4])
    errors = -torch.logsumexp(errors, dim=-1, keepdim=True)
    return torch.mean(errors)


def pytorch_neg_multi_log_likelihood_batch(gt, predictions, confidences, avails):
    """
    Compute a negative log-likelihood for the multi-modal scenario.
    Args:
        gt (Tensor): array of shape (bs)x(time)x(2D coords)
        predictions (Tensor): array of shape (bs)x(modes)x(time)x(2D coords)
        confidences (Tensor): array of shape (bs)x(modes) with a confidence for each mode in each sample
        avails (Tensor): array of shape (bs)x(time) with the availability for each gt timestep
    Returns:
        Tensor: negative log-likelihood for this example, a single float number
    """
    gt = torch.unsqueeze(gt, 1)  # add modes
    avails = avails[:, None, :, None]  # add modes and cords
    error = torch.sum(
        ((gt - predictions) * avails) ** 2, dim=-1
    )  # reduce coords and use availability
    with np.errstate(
        divide="ignore"
    ):  # when confidence is 0 log goes to -inf, but we're fine with it
        # error (batch_size, num_modes)
        error = nn.functional.log_softmax(confidences, dim=1) - 0.5 * torch.sum(
            error, dim=-1
        )  # reduce time
    # error (batch_size, num_modes)
    error = -torch.logsumexp(error, dim=-1, keepdim=True)
    return torch.mean(error)