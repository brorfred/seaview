"""
Utility functions for generating colorbar images.
"""

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.cm as cm
import base64
from io import BytesIO


def generate_colorbar_image(cmap_name, vmin, vmax, label='', height=150, width=30, 
                           ticks=None, tick_labels=None):
    """
    Generate a base64-encoded colorbar image using matplotlib.
    
    This function creates a vertical colorbar as a PNG image and encodes it
    in base64 format for embedding in HTML.
    
    Parameters
    ----------
    cmap_name : str or matplotlib.colors.Colormap
        The colormap to use. Can be a string name (e.g., 'viridis', 'RdYlBu_r')
        or a matplotlib colormap object.
    vmin : float
        Minimum value for the colorbar scale
    vmax : float
        Maximum value for the colorbar scale
    label : str, default ''
        Label text to display alongside the colorbar
    height : int, default 150
        Height of the colorbar in pixels
    width : int, default 30
        Width of the colorbar in pixels
    ticks : list of float, optional
        Custom tick positions. If None, matplotlib will determine ticks automatically.
        Example: [0, 10, 20, 30, 40]
    tick_labels : list of str, optional
        Custom tick labels corresponding to tick positions. If None, uses the tick
        values as labels.
        Example: ['Low', 'Med', 'High', 'Very High']
    
    Returns
    -------
    str
        Base64-encoded PNG image string
    
    Examples
    --------
    Basic colorbar:
    
    >>> img = generate_colorbar_image('viridis', 0, 100, 'Temperature (°C)')
    
    Categorical colorbar:
    
    >>> img = generate_colorbar_image(
    ...     'RdYlGn', 0, 3, 'Risk Level',
    ...     ticks=[0, 1, 2, 3],
    ...     tick_labels=['Low', 'Medium', 'High', 'Critical']
    ... )
    
    Minimal ticks:
    
    >>> img = generate_colorbar_image(
    ...     'plasma', 0, 1000, 'Population',
    ...     ticks=[0, 500, 1000]
    ... )
    
    Notes
    -----
    - The generated image has a transparent background
    - Font sizes are optimized for small displays (6.5pt for ticks, 7.5pt for labels)
    - The figure is automatically closed after generation to prevent memory leaks
    """
    # Create figure with tight layout
    fig_height = height / 80
    fig_width = width / 80
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    fig.subplots_adjust(left=0.05, right=0.35, top=0.98, bottom=0.02)
    
    # Get colormap
    if isinstance(cmap_name, str):
        cmap = plt.colormaps.get_cmap(cmap_name)
    else:
        cmap = cmap_name
    
    # Create normalization and colorbar
    norm = Normalize(vmin=vmin, vmax=vmax)
    cb = plt.colorbar(
        cm.ScalarMappable(norm=norm, cmap=cmap),
        cax=ax,
        orientation='vertical'
    )
    
    # Set custom ticks if provided
    if ticks is not None:
        cb.set_ticks(ticks)
        if tick_labels is not None:
            cb.set_ticklabels(tick_labels)
    
    # Set label with smaller font
    if label:
        cb.set_label(label, rotation=270, labelpad=12, fontsize=7.5)
    
    # Style the colorbar - smaller ticks
    cb.ax.tick_params(labelsize=6.5, length=2, width=0.5, pad=2)
    cb.outline.set_linewidth(0.5)
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', 
               dpi=120, transparent=True, facecolor='none')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return img_base64
