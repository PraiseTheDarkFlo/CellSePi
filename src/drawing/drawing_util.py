

def mask_shifting(mask_data,deleted_mask_id:int):
    """
    Shifts the mask when a mask got deleted to restore an order without gaps.

    Args:
        mask_data (np.array): the mask data.
        deleted_mask_id (int): the id of the deleted mask.

    Raises:
          ValueError: if the deleted_mask_id is smaller or equal to 0.
    """
    if deleted_mask_id < 1:
        raise ValueError("deleted_mask_id must be greater than 0")

    mask = mask_data["masks"]
    outline = mask_data["outlines"]

    mask[mask>deleted_mask_id] -= 1
    outline[outline>deleted_mask_id] -= 1
