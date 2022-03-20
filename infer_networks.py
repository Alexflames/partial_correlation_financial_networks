import pandas as pd
import numpy as np
import math
import networkx as nx
from sklearn.preprocessing import StandardScaler
import os
from sklearn.covariance import LedoitWolf
import matplotlib.pyplot as plt
from os import makedirs

def precision_matrix_to_partial_corr(theta):
    """
    Turns a precision matrix into a partial correlation one
    """
    p = theta.shape[0]
    partial_corr = np.zeros((p, p))
    for i in range(p):
        for j in range(p):
            partial_corr[i, j] = -theta[i, j] / np.sqrt(theta[i, i] * theta[j, j])
    np.fill_diagonal(partial_corr, 1)
    return partial_corr

def covariance_matrix_to_corr(cov):
    """
    Turns a covariance matrix into a correlation one
    """
    p = cov.shape[0]
    corr = np.zeros((p, p))
    for i in range(p):
        for j in range(p):
            corr[i, j] = cov[i, j] / np.sqrt(cov[i, i] * cov[j, j])
    np.fill_diagonal(corr, 1)
    return corr


def run(**params):
    np.seterr(all='raise')

    df = pd.read_csv(params["input_name"], index_col=0)

    company_sectors = df.iloc[0, :].values
    company_names = df.T.index.values
    sectors = list(sorted(set(company_sectors)))
    df_2 = df.iloc[1:, :]
    df_2 = df_2.apply(pd.to_numeric)
    df_2 = np.log(df_2) - np.log(df_2.shift(1))
    X = df_2.values[1:, :]

    shrinkages = []

    window_size = 300
    slide_size = 30
    no_samples = X.shape[0]
    p = X.shape[1]
    no_runs = math.floor((no_samples - window_size) / (slide_size))
    print("We're running %s times" % no_runs)

    X_new = X[0:window_size, :]
    ss = StandardScaler()
    X_new = ss.fit_transform(X_new)

    lw = LedoitWolf()
    lw.fit(X_new)
    shrinkages.append(lw.shrinkage_)

    corr = lw.covariance_

    prec = lw.precision_
    corr = covariance_matrix_to_corr(corr)
    prec = precision_matrix_to_partial_corr(prec)
    l=0
    
    os.makedirs(params['cor_dir'], exist_ok=True)
    os.makedirs(params['pcor_dir'], exist_ok=True)

    G=nx.from_numpy_matrix(corr)
    G=nx.relabel_nodes(G, dict(zip(G.nodes(), company_names)))
    node_attributes = dict(zip(company_names[list(range(len(company_sectors)))], company_sectors))
    nx.set_node_attributes(G, node_attributes, 'sector')
    G.graph['l'] = l
    nx.write_graphml(G, params['cor_dir'] + "network_over_time_corr_%s.graphml" % 0)
    makedirs(params['cor_dir'] + "edgelists/", exist_ok=True)
    nx.write_edgelist(G, params['cor_dir'] + "edgelists/" + "network_over_time_pecorr_%s.txt" % 0)
    print("%s non-zero values" % np.count_nonzero(prec))
    
    np.save(params['workdir'] + "prec_0", prec)

    G=nx.from_numpy_matrix(prec)
    G=nx.relabel_nodes(G, dict(zip(G.nodes(), company_names)))
    node_attributes = dict(zip(company_names[list(range(len(company_sectors)))], company_sectors))
    nx.set_node_attributes(G, node_attributes, 'sector')
    G.graph['l'] = l
    nx.write_graphml(G, params['pcor_dir'] + "network_over_time_prec_%s.graphml" % 0)
    makedirs(params['pcor_dir'] + "edgelists/", exist_ok=True)
    nx.write_edgelist(G, params['pcor_dir'] + "edgelists/" + "network_over_time_pacorr_%s.txt" % 0)

    par_corr_values = []
    corr_values = []

    corr_values.append(corr.flatten())
    par_corr_values.append(prec.flatten())
    prev_prec = prec.copy()

    for x in range(1, no_runs):
        print("Run %s" % x)
        X_new = X[x*slide_size:(x+1)*slide_size+window_size, :]

        ss = StandardScaler()
        X_new = ss.fit_transform(X_new)

        lw = LedoitWolf()
        lw.fit(X_new)

        shrinkages.append(lw.shrinkage_)
        corr = covariance_matrix_to_corr(lw.covariance_)

        prec = lw.precision_
        prec = precision_matrix_to_partial_corr(prec)

        corr_values.append(corr.flatten())
        par_corr_values.append(prec.flatten())
        G=nx.from_numpy_matrix(corr)
        G=nx.relabel_nodes(G, dict(zip(G.nodes(), company_names)))
        node_attributes = dict(zip(company_names[list(range(len(company_sectors)))], company_sectors))
        nx.set_node_attributes(G, node_attributes, 'sector')
        nx.write_graphml(G, params['cor_dir'] + "network_over_time_corr_%s.graphml" % x)
        nx.write_edgelist(G, params['cor_dir'] + "edgelists/" + "network_over_time_pecorr_%s.txt" % x)

        G=nx.from_numpy_matrix(prec)
        G=nx.relabel_nodes(G, dict(zip(G.nodes(), company_names)))
        node_attributes = dict(zip(company_names[list(range(len(company_sectors)))], company_sectors))
        nx.set_node_attributes(G, node_attributes, 'sector')
        nx.write_graphml(G, params['pcor_dir'] + "network_over_time_prec_%s.graphml" % x)
        nx.write_edgelist(G, params['pcor_dir'] + "edgelists/" + "network_over_time_pacorr_%s.txt" % x)

    plt.figure()
    plt.hist(corr_values)
    plt.title("Edge Weight Distribution")
    axes = plt.gca()
    axes.set_ylim([0,13000])
    plt.savefig(params['output_dest'] + "correlation_values.png")
    plt.figure()
    plt.hist(par_corr_values)
    plt.title("Edge Weight Distribution")
    axes = plt.gca()
    axes.set_ylim([0,13000])
    plt.savefig(params['output_dest'] + "partial_correlation_values.png")

    plt.figure()
    plt.plot(shrinkages, label="Shrinkages")   
    plt.savefig(params['output_dest'] + "shrinkages.png")

    plt.show()
    print("")


if __name__ == "__main__":
	run()
