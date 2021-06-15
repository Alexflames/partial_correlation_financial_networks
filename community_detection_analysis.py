import numpy as np
import scipy.stats as sts
import matplotlib.pyplot as plt
from scipy.stats import distributions
import pandas as pd
import math
import louvain_cython as lcn


def run(**params):
    df = pd.read_csv(params['input_name'], index_col=0)
    company_sectors = df.iloc[0, :].values
    company_names = df.T.index.values
    sectors = list(sorted(set(company_sectors)))
    num_sectors = len(sectors)
    company_sector_lookup = {}

    for i,comp in enumerate(company_names):
        company_sector_lookup[comp] = company_sectors[i]

    df_2 = df.iloc[1:, :]
    df_2 = df_2.apply(pd.to_numeric)
    df_2 = np.log(df_2) - np.log(df_2.shift(1))
    X = df_2.values[1:, :]

    window_size = 300
    slide_size = 30
    no_samples = X.shape[0]
    p = X.shape[1]
    no_runs = math.floor((no_samples - window_size)/ (slide_size))
    dates = []

    for x in range(no_runs):
        dates.append(df.index[(x+1)*slide_size+window_size][0:10])
    dt = pd.to_datetime(dates)
    dt_2 = dt[1:]
    networks_folder_correlation = params['cor_dir']
    networks_folder_partial_correlation = params['pcor_dir']


    # Read in the correlation and partial correlation results
    cluster_consistency_mean_corr = np.load(params['cor_dir']+"np/cluster_consistency_mean_.npy")
    cluster_consistency_mean_par_corr = np.load(params['pcor_dir']+"np/cluster_consistency_mean_.npy")
    cluster_consistency_stdev_corr = np.load(params['cor_dir']+"np/cluster_consistency_stdev_.npy")
    cluster_consistency_stdev_par_corr = np.load(params['pcor_dir']+"np/cluster_consistency_stdev_.npy")

    num_clusters_mean_corr = np.load(params['cor_dir']+"np/num_clusters_mean_.npy")
    num_clusters_mean_par_corr = np.load(params['pcor_dir']+"np/num_clusters_mean_.npy")
    num_clusters_stdev_corr = np.load(params['cor_dir']+"np/num_clusters_stdev_.npy")
    num_clusters_stdev_par_corr = np.load(params['pcor_dir']+"np/num_clusters_stdev_.npy")

    rand_scores_mean_corr = np.load(params['cor_dir']+"np/rand_scores_mean_.npy")
    rand_scores_mean_par_corr = np.load(params['pcor_dir']+"np/rand_scores_mean_.npy")
    rand_scores_stdev_corr = np.load(params['cor_dir']+"np/rand_scores_stdev_.npy")
    rand_scores_stdev_par_corr = np.load(params['pcor_dir']+"np/rand_scores_stdev_.npy")

    rand_scores_mean = pd.DataFrame()
    rand_scores_stdev = pd.DataFrame()
    ts = pd.Series(rand_scores_mean_corr, index=dt)
    rand_scores_mean['Correlation'] = ts
    ts = pd.Series(rand_scores_mean_par_corr, index=dt)
    rand_scores_mean['Partial Correlation'] = ts

    ts = pd.Series(rand_scores_stdev_corr, index=dt)
    rand_scores_stdev['Correlation'] = ts
    ts = pd.Series(rand_scores_stdev_par_corr, index=dt)
    rand_scores_stdev['Partial Correlation'] = ts

    ax = rand_scores_mean.plot(yerr=rand_scores_stdev)
    plt.title("Rand Score")
    plt.savefig(params['output_dest']+"rand_score.png")
    #ax.set_ylim(0, 1)

    number_clusters_mean_df = pd.DataFrame()
    number_clusters_stdev_df = pd.DataFrame()
    ts = pd.Series(num_clusters_mean_corr, index=dt)
    number_clusters_mean_df['Correlation'] = ts
    ts = pd.Series(num_clusters_mean_par_corr, index=dt)
    number_clusters_mean_df['Partial Correlation'] = ts

    ts = pd.Series(num_clusters_stdev_corr, index=dt)
    number_clusters_stdev_df['Correlation'] = ts
    ts = pd.Series(num_clusters_stdev_par_corr, index=dt)
    number_clusters_stdev_df['Partial Correlation'] = ts

    ax = number_clusters_mean_df.plot(yerr=number_clusters_stdev_df)
    plt.title("Mean Number of Clusters")
    plt.savefig(params['output_dest']+"num_clusters.png")

    cluster_consistency_mean_df = pd.DataFrame()
    cluster_consistency_stdev_df = pd.DataFrame()
    ts = pd.Series(cluster_consistency_mean_corr, index=dt_2)
    cluster_consistency_mean_df['Correlation'] = ts
    ts = pd.Series(cluster_consistency_mean_par_corr, index=dt_2)
    cluster_consistency_mean_df['Partial Correlation'] = ts

    ts = pd.Series(cluster_consistency_stdev_corr, index=dt_2)
    cluster_consistency_stdev_df['Correlation'] = ts
    ts = pd.Series(cluster_consistency_stdev_par_corr, index=dt_2)
    cluster_consistency_stdev_df['Partial Correlation'] = ts

    ax = cluster_consistency_mean_df.plot(yerr=cluster_consistency_stdev_df)
    plt.title("Clustering Consistency")
    plt.savefig(params['output_dest']+"clustering_consistency.png")


    plt.show()


if __name__ == "__main__":
	run()
