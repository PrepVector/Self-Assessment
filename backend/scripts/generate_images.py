import os
import matplotlib.pyplot as plt
import numpy as np

PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "images")

# ─── Data Visualization Generators (Batch 1) ──────────────────────────────

def generate_confusion_matrix_1(fig, ax):
    data = np.array([[50, 10], [5, 35]])
    ax.imshow(data, cmap='Blues', vmin=0, vmax=60, alpha=0.8)
    for (i, j), val in np.ndenumerate(data):
        ax.text(j, i, f'{val}', ha='center', va='center', color='white', fontweight='bold', fontsize=14)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Predicted 0', 'Predicted 1'], color='white')
    ax.set_yticklabels(['Actual 0', 'Actual 1'], color='white')
    ax.set_title("Confusion Matrix", color='white', pad=15)

def generate_boxplot(fig, ax):
    np.random.seed(42)
    data = np.random.normal(50, 15, 200)
    boxprops = dict(facecolor='#3b82f6', color='white')
    medianprops = dict(color='#fbbf24', linewidth=2.5) 
    whiskerprops = dict(color='white', linewidth=1.5)
    capprops = dict(color='white', linewidth=1.5)
    flierprops = dict(marker='o', markerfacecolor='white', markeredgecolor='none', alpha=0.5)
    
    # Removed the 'labels' argument from this call
    ax.boxplot(data, patch_artist=True, boxprops=boxprops, medianprops=medianprops, 
               whiskerprops=whiskerprops, capprops=capprops, flierprops=flierprops)
    
    # Added manual, version-proof tick labeling
    ax.set_xticks([1])
    ax.set_xticklabels(['Dataset'], color='white')
    
    ax.set_ylabel("Value", color='gray')
    ax.set_title("Distribution Boxplot", color='white', pad=15)
def generate_non_linear_residual_plot(fig, ax):
    np.random.seed(42)
    x = np.random.uniform(-3, 3, 150)
    residuals = 1.5 * (x**2) - 4.5 + np.random.normal(0, 1.5, 150)
    ax.scatter(x, residuals, color='#3b82f6', alpha=0.7, edgecolors='w', linewidth=0.5)
    ax.axhline(0, color='gray', linestyle='--', linewidth=2)
    ax.set_xlabel("Predictor Variable", color='gray')
    ax.set_ylabel("Residuals", color='gray')
    ax.set_title("Model Residuals", color='white', pad=15)

def generate_overconfident_calibration(fig, ax):
    prob_pred = np.linspace(0.05, 0.95, 10)
    prob_true = 0.5 + 0.6 * (prob_pred - 0.5)
    ax.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfectly Calibrated')
    ax.plot(prob_pred, prob_true, marker='o', color='#ef4444', linewidth=2, markersize=8, label='Model')
    ax.set_xlabel('Mean Predicted Probability', color='gray')
    ax.set_ylabel('Fraction of Positives', color='gray')
    ax.set_title("Calibration Curve", color='white', pad=15)
    legend = ax.legend(loc="lower right", facecolor='#0f172a', edgecolor='gray')
    for text in legend.get_texts(): text.set_color("white")

def generate_colormap_comparison(fig, ax):
    ax.remove() 
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    X, Y = np.meshgrid(np.linspace(-3, 3, 100), np.linspace(-3, 3, 100))
    Z = np.exp(-(X**2 + Y**2) / 2) 
    ax1.imshow(Z, cmap='jet')
    ax1.set_title("Colormap A", color='white')
    ax1.axis('off')
    ax2.imshow(Z, cmap='viridis')
    ax2.set_title("Colormap B", color='white')
    ax2.axis('off')
    fig.suptitle("2D Gaussian Mixture", color='white', y=0.95)

def generate_heteroscedasticity_plot(fig, ax):
    np.random.seed(101)
    fitted_values = np.linspace(10, 100, 200)
    residuals = np.random.normal(0, fitted_values * 0.15)
    ax.scatter(fitted_values, residuals, color='#3b82f6', alpha=0.7, edgecolors='w', linewidth=0.5)
    ax.axhline(0, color='gray', linestyle='--', linewidth=2)
    ax.set_xlabel("Fitted Values", color='gray')
    ax.set_ylabel("Residuals", color='gray')
    ax.set_title("Residual Plot", color='white', pad=15)

def generate_right_skewed_density(fig, ax):
    x = np.linspace(0, 15, 500)
    y = (x * np.exp(-x / 2)) / 4 
    ax.plot(x, y, color='#3b82f6', linewidth=2)
    ax.fill_between(x, y, color='#3b82f6', alpha=0.3)
    ax.axvline(2, color='#ef4444', linestyle='--', linewidth=2, label='Mode')
    ax.axvline(3.35, color='#fbbf24', linestyle='--', linewidth=2, label='Median')
    ax.axvline(4, color='#10b981', linestyle='--', linewidth=2, label='Mean')
    ax.set_xlabel("Value", color='gray')
    ax.set_ylabel("Density", color='gray')
    ax.set_title("Data Distribution", color='white', pad=15)
    legend = ax.legend(loc="upper right", facecolor='#0f172a', edgecolor='gray')
    for text in legend.get_texts(): text.set_color("white")

# ─── Machine & Applied Stats Generators (Batch 2) ───────────────────────

def generate_qq_plot_heavy_tails(fig, ax):
    theoretical = np.linspace(-3, 3, 100)
    sample = theoretical + 0.4 * (theoretical ** 3) # Creates heavy tail S-shape
    ax.plot([-5, 5], [-5, 5], linestyle='--', color='gray', linewidth=2, label='Normal Distribution')
    ax.scatter(theoretical, sample, color='#3b82f6', alpha=0.8, edgecolors='w', linewidth=0.5)
    ax.set_xlim(-4, 4)
    ax.set_ylim(-6, 6)
    ax.set_xlabel("Theoretical Quantiles", color='gray')
    ax.set_ylabel("Sample Quantiles", color='gray')
    ax.set_title("Normal Q-Q Plot", color='white', pad=15)

def generate_confusion_matrix_2(fig, ax):
    data = np.array([[90, 10], [5, 45]])
    ax.imshow(data, cmap='Blues', vmin=0, vmax=100, alpha=0.8)
    for (i, j), val in np.ndenumerate(data):
        ax.text(j, i, f'{val}', ha='center', va='center', color='white', fontweight='bold', fontsize=14)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Pred Negative', 'Pred Positive'], color='white')
    ax.set_yticklabels(['Actual Negative', 'Actual Positive'], color='white')
    ax.set_title("Binary Confusion Matrix", color='white', pad=15)

def generate_roc_curve_comparison(fig, ax):
    fpr = np.linspace(0, 1, 100)
    tpr_a = fpr ** 0.15 # AUC ~0.92
    tpr_b = fpr ** 0.65 # AUC ~0.75
    ax.plot(fpr, tpr_a, color='#10b981', linewidth=2.5, label='Model A (AUC = 0.92)')
    ax.plot(fpr, tpr_b, color='#3b82f6', linewidth=2.5, label='Model B (AUC = 0.75)')
    ax.plot([0, 1], [0, 1], 'k--', color='gray')
    ax.set_xlabel("False Positive Rate", color='gray')
    ax.set_ylabel("True Positive Rate", color='gray')
    ax.set_title("ROC Curve Comparison", color='white', pad=15)
    legend = ax.legend(loc="lower right", facecolor='#0f172a', edgecolor='gray')
    for text in legend.get_texts(): text.set_color("white")

def generate_learning_curve_high_bias(fig, ax):
    x = np.linspace(10, 200, 50)
    train_err = 0.40 - (0.25 / np.sqrt(x))
    val_err = 0.43 + (0.30 / np.sqrt(x))
    ax.plot(x, train_err, color='#3b82f6', linewidth=2.5, label='Training Error')
    ax.plot(x, val_err, color='#ef4444', linewidth=2.5, label='Validation Error')
    ax.set_ylim(0, 0.6)
    ax.set_xlabel("Training Set Size", color='gray')
    ax.set_ylabel("Error", color='gray')
    ax.set_title("Learning Curves", color='white', pad=15)
    legend = ax.legend(loc="center right", facecolor='#0f172a', edgecolor='gray')
    for text in legend.get_texts(): text.set_color("white")

def generate_pca_scree_plot(fig, ax):
    components = np.arange(1, 9)
    explained_variance = [45, 25, 15, 6, 4, 2.5, 1.5, 1]
    ax.plot(components, explained_variance, marker='o', color='#3b82f6', linewidth=2.5, markersize=8)
    ax.axvline(3, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel("Principal Component", color='gray')
    ax.set_ylabel("Explained Variance (%)", color='gray')
    ax.set_title("Scree Plot", color='white', pad=15)

def generate_shap_summary_plot(fig, ax):
    np.random.seed(42)
    features = ['MonthlyCharges', 'Tenure', 'Contract', 'OnlineSecurity']
    y_pos = [4, 3, 2, 1]
    
    for i, feature in enumerate(features):
        x_vals = np.random.normal(0, 1.5 if i < 2 else 0.8, 200)
        # Simulate coloring: OnlineSecurity 'no' (blue) is high risk (positive SHAP)
        if feature == 'OnlineSecurity' or feature == 'Contract':
            colors = np.where(x_vals > 0, '#3b82f6', '#ef4444') # Blue on right, red on left
        else:
            colors = np.where(x_vals > 0, '#ef4444', '#3b82f6') # Red on right, blue on left
        
        y_jitter = y_pos[i] + np.random.normal(0, 0.08, 200)
        ax.scatter(x_vals, y_jitter, c=colors, alpha=0.6, s=15)

    ax.axvline(0, color='gray', linestyle='-', alpha=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(features, color='white')
    ax.set_xlabel("SHAP value (impact on model output)", color='gray')
    ax.set_title("SHAP Summary Plot", color='white', pad=15)

# ─── Main Execution ──────────────────────────────────────────────────────

def main():
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    plt.style.use('dark_background')
    
    image_generators = {
        # Batch 1
        "dataviz_easy_q3_confusion_matrix.png": generate_confusion_matrix_1,
        "dataviz_easy_q5_boxplot.png": generate_boxplot,
        "data_visualization_moderate_q1_residual_plot.png": generate_non_linear_residual_plot,
        "data_visualization_moderate_q4_calibration_curve.png": generate_overconfident_calibration,
        "data_visualization_advanced_q1_calibration_curve.png": generate_overconfident_calibration,
        "data_visualization_advanced_q3_colormap_comparison.png": generate_colormap_comparison,
        "heteroscedasticity_residual_plot.png": generate_heteroscedasticity_plot,
        "right_skewed_density_plot.png": generate_right_skewed_density,
        "heteroscedasticity_residuals.png": generate_heteroscedasticity_plot,
        
        # Batch 2
        "qq_plot_heavy_tails.png": generate_qq_plot_heavy_tails,
        "residual_heteroscedasticity.png": generate_heteroscedasticity_plot,
        "confusion_matrix_example.png": generate_confusion_matrix_2,
        "roc_curve_comparison.png": generate_roc_curve_comparison,
        "learning_curves_high_bias.png": generate_learning_curve_high_bias,
        "pca_scree_plot.png": generate_pca_scree_plot,
        "calibration_plot_example.png": generate_overconfident_calibration,
        "shap_summary_plot.png": generate_shap_summary_plot
    }

    for filename, func in image_generators.items():
        fig, ax = plt.subplots(figsize=(6, 4.5))
        func(fig, ax)
        
        if "colormap" not in filename:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('gray')
            ax.spines['bottom'].set_color('gray')
            ax.tick_params(colors='gray')
            
            if "confusion_matrix" not in filename and "shap" not in filename:
                ax.grid(True, color='#333333', linestyle='--', alpha=0.5)
        
        save_path = os.path.join(PUBLIC_DIR, filename)
        fig.savefig(save_path, bbox_inches='tight', facecolor='#0f172a', dpi=150) 
        plt.close(fig)
        print(f"✅ Generated production plot: {filename}")

if __name__ == "__main__":
    main()