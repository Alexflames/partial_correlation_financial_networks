import numpy as np
import matplotlib.pyplot as plt
import collections
import scipy
import math
import networkx as nx
from scipy.stats import norm, spearmanr
import os
import pandas as pd
import seaborn as sns
from pathlib import Path
import operator
import matplotlib
from sklearn.preprocessing import StandardScaler
from statsmodels.stats import multitest


def get_centrality(G, degree=True, prec=None, p=0):
    """
    Calculates the centrality of each node and mean centrality of a sector 
    if degree is true we use degree centrality, if not we use eigenvector centrality
    """
    node_centrality = collections.defaultdict(float)
    total = 0

    if not degree:
        # Do eigenvector centrality
        M = nx.to_numpy_matrix(G)
        _, eigv = scipy.linalg.eigh(prec, eigvals=(p-1, p-1))
        total = eigv.sum()
        for i,node in enumerate(G.nodes):
            node_centrality[node] = eigv[i][0]/total
    else:
        # Calculate the weighted edge centrality
        for node in G.nodes:
            for edge in G[node]:
                node_centrality[node] += G[node][edge]['weight']
                total += G[node][edge]['weight']

        # Normalise so the total is 1
        for comp in node_centrality:
            node_centrality[comp] = node_centrality[comp]/total

    sorted_centrality = sort_dict(node_centrality)
    centrality_names = [x[0] for x in sorted_centrality]
    centrality_sectors = []

    for name in centrality_names:
        centrality_sectors.append(G.nodes[name]['sector'])

    # Figure out the mean centrality of a sector
    sector_centrality = collections.defaultdict(float)
    no_companies_in_sector = collections.defaultdict(int)

    for comp in G:
        sector = G.nodes[comp]['sector']
        sector_centrality[sector] += node_centrality[comp]
        no_companies_in_sector[sector] += 1
    for sec in sector_centrality:
        sector_centrality[sec] /= no_companies_in_sector[sec]

    return node_centrality, sector_centrality

def turn_dict_into_np_array(dct, company_names):
    """
    Turns the dct into a numpy array where the keys are held in company_names
    """
    company_names = list(company_names)
    ret_arr = np.zeros(len(company_names))
    for key in dct:
        i = company_names.index(key)
        ret_arr[i] = dct[key]

    return ret_arr


def sort_dict(dct):
    """
    Takes a dict and returns a sorted list of key value pairs
    """
    sorted_x = sorted(dct.items(), key=operator.itemgetter(1), reverse=True)

    return sorted_x

def save_open_figures(prefix=""):
    """
    Saves all open figures
    """
    figures=[manager.canvas.figure
         for manager in matplotlib._pylab_helpers.Gcf.get_all_fig_managers()]

    for i, figure in enumerate(figures):
        mng = plt.get_current_fig_manager()
        #mng.resize(*mng.window.maxsize())
        figure.savefig(prefix+'figure%d.png' % i)

def get_sector_full_nice_name(sector):
    """
    Returns a short version of the sector name
    """       
    if sector == "technology":
        return "Technology + Communication Services"
    elif sector == 'communication_services':
        return "Technology + Communication Services"
    elif sector == "real_estate":
        return "Real Estate"
    elif sector == "basic_materials":
        return "Basic Materials"
    elif sector == "energy":
        return "Energy"
    elif sector == "financial_services":
        return "Financials"
    elif sector == "utilities":
        return "Utilities"
    elif sector == "industrials":
        return "Industrials"
    elif sector == "consumer_cyclical":
        return "Consumer Cyclical"
    elif sector == "healthcare":
        return "Healthcare"
    elif sector == "consumer_defensive":
        return "Consumer Defensive"
    else:
        raise Exception("%s is not a valid sector" % sector)


def run(**params):
    #df = pd.DataFrame.from_csv("s_and_p_500_sector_tagged.csv")
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
    no_runs = math.floor((no_samples - window_size) / (slide_size))
    dates = []

    for x in range(no_runs-1):
        dates.append(df.index[(x+1)*slide_size+window_size][0:10])

    dates_2 = []

    for x in range(no_runs):
        dates_2.append(df.index[(x+1)*slide_size+window_size][0:10])

    # Change this if you wish to analyze either correlation or partial correlation networks
    for folder in [params['cor_dir'], params['pcor_dir']]:
        network_type = folder.split('/')[1]
        networks_folder = folder
        onlyfiles = [os.path.abspath(os.path.join(networks_folder, f)) for f in os.listdir(networks_folder) if os.path.isfile(os.path.join(networks_folder, f))]
        #onlyfiles = onlyfiles[0:1]
        #onlyfiles = list(map(lambda x: os.path.splitext(x)[0], onlyfiles))
        Graphs = []

        # Sort the files into order
        ind = [int(Path(x).stem[23:]) for x in onlyfiles]
        ind = np.argsort(np.array(ind))

        for i in ind:
            f = onlyfiles[i]
            G = nx.read_graphml(f)
            Graphs.append(G)

        number_graphs = len(Graphs)
        number_companies = len(G)

        sector_centrality_lst_degree = []
        node_centrality_lst_degree = []
        sector_centrality_lst_eigv = []
        node_centrality_lst_eigv = []

        sharpe_ratios = np.zeros(number_graphs*number_companies)
        centralities_degree = np.zeros(number_companies*number_graphs)
        centralities_eigv = np.zeros(number_companies*number_graphs)

        risks = np.zeros(number_companies*number_graphs)
        ls = []
        edge_weights = []

        max_eigs = np.zeros(no_runs)

        max_eigv = np.zeros((no_runs, p))
        max_eigv_diff = np.zeros(no_runs-1)

        for i,G in enumerate(Graphs):
            prec = np.array(nx.to_numpy_matrix(G))
            eigs, eigv = scipy.linalg.eigh(prec, eigvals=(p-1, p-1))
            max_eigs[i] = eigs
            eigv = eigv/eigv.sum()
            max_eigv[i, :] = eigv.flatten()
            if i > 0:
                max_eigv_diff[i-1] = np.linalg.norm(max_eigv[i-1,:] - eigv)

            node_centrality_degree, sector_centrality_degree = get_centrality(G)
            node_centrality_eigv, sector_centrality_eigv = get_centrality(G, degree=False, prec=prec, p=p)

            sector_centrality_lst_degree.append(sector_centrality_degree)
            node_centrality_lst_degree.append(node_centrality_degree)
            sector_centrality_lst_eigv.append(sector_centrality_eigv)
            node_centrality_lst_eigv.append(node_centrality_eigv)

            edge_weights.append(prec.flatten())

            X_new = X[x*slide_size:(x+1)*slide_size+window_size, :]
            S = np.cov(X_new.T)
            ret = np.mean(X_new, axis=0)

            # Look at the returns
            if i + 1 < number_graphs:
                X_new = X[(i+1)*slide_size:(i+2)*slide_size+window_size, :]
            ret = np.mean(X_new, axis=0)
            risk = np.std(X_new, axis=0)
            
            np.seterr(divide='warn', invalid='warn')
            sharpe = np.divide(ret, risk)
            degree_centrality = turn_dict_into_np_array(node_centrality_degree, company_names)
            eigv_centrality = turn_dict_into_np_array(node_centrality_eigv, company_names)

            sharpe_ratios[i*number_companies:(i+1)*number_companies] = sharpe.flatten()
            centralities_degree[i*number_companies:(i+1)*number_companies] = degree_centrality
            risks[i*number_companies:(i+1)*number_companies] = risk.flatten()
            centralities_eigv[i*number_companies:(i+1)*number_companies] = eigv_centrality
        
        f = open(params['output_dest']+'eigv_centralities_'+network_type, 'w')
        for company_name in company_names:
            f.write(company_name + ';')
        f.write('\n')

        for i in range(len(Graphs)):
            for j in range(number_companies):
                f.write(str(centralities_eigv[i*number_companies + j]) + ';')
            f.write('\n')
        f.close()
    
        f = open(params['output_dest']+'correlation_'+network_type, 'w')
        f.write("Correlation between degree centrality and Sharpe Ratio: (" + network_type + ")\n")
        f.write(str(spearmanr(centralities_degree, sharpe_ratios)))
        f.write("\n")

        f.write("Correlation between degree centrality and risks \n")
        f.write(str(spearmanr(centralities_degree, risks)))
        f.write("\n")

        f.write("Correlation between eigenvector centrality and Sharpe Ratio:\n")
        f.write(str(spearmanr(centralities_eigv, sharpe_ratios)))
        f.write("\n")

        f.write("Correlation between eigenvector centrality and risks\n")
        f.write(str(spearmanr(centralities_eigv, risks)))
        f.close()

        dt = pd.to_datetime(dates_2)
        dt_2 = pd.to_datetime(dates)

        ts = pd.Series(max_eigs, index=dt)
        plt.figure()
        ts.plot()
        plt.title("Largest Eigenvalue")

        ts = pd.Series(max_eigv_diff, index=dt_2)
        plt.figure()
        ts.plot()
        plt.title("Largest Eigenvector Diff")
        ax = plt.gca()
        ax.set_ylim(0, 1.5)

        sector_centrality_over_time = collections.defaultdict(list)
        ss = []
        for centrality in sector_centrality_lst_degree: 
            s = sum(centrality.values())
            ss.append(s)
            #s = 1
            for sector in centrality:
                sector_centrality_over_time[sector].append(centrality[sector]/s)

        sector_centrality = pd.DataFrame()
        for sector in sector_centrality_over_time:
            ts = pd.Series(sector_centrality_over_time[sector], index=dt)
            sector_nice_name = get_sector_full_nice_name(sector)
            sector_centrality[sector_nice_name] = ts

        sector_centrality.plot(color = ['#1f77b4', '#aec7e8', '#ff7f0e', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#ff9896'], legend=False)
        plt.title("Degree Centrality")
        plt.ylim(0, 0.20)

        sector_centrality_over_time = collections.defaultdict(list)
        ss = []
        for centrality in sector_centrality_lst_eigv: 
            s = sum(centrality.values())
            ss.append(s)
            #s = 1
            for sector in centrality:
	            sector_centrality_over_time[sector].append(centrality[sector]/s)

        sector_centrality = pd.DataFrame()
        for sector in sector_centrality_over_time:
            ts = pd.Series(sector_centrality_over_time[sector], index=dt)
            sector_nice_name = get_sector_full_nice_name(sector)
            sector_centrality[sector_nice_name] = ts
        sector_centrality.plot(color = ['#1f77b4', '#aec7e8', '#ff7f0e', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#ff9896'], legend=False)
        plt.title("Eigenvector Centrality")
        plt.ylim(0, 0.20)
        save_open_figures(params['output_dest']+network_type+"_financial_networks_graphml_")
        plt.close('all')

	
if __name__ == "__main__":
	run()
