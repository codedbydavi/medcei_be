#simulation_engine.py

def run_sir(current_state, params):
    # Garantia de Tipos (Cast)
    S = float(current_state['s_initial'])
    I = float(current_state['i_initial'])
    R = float(current_state.get('r_initial', 0))
    day = int(current_state['day'])

    N = float(params['population'])
    beta = float(params['beta'])
    gamma = float(params['gamma'])

    transmission = (beta * S * I) / N
    recuperation = gamma * I

    S_new = S - transmission
    I_new = I + transmission - recuperation
    R_new = R + recuperation

    return {
        'day': day + 1,
        'S': max(0, S_new),
        'I': max(0, I_new),
        'R': max(0, R_new),
        'D': 0
    }

def run_sird(current_state, params):
    S = float(current_state['S'])
    I = float(current_state['I'])
    R = float(current_state['R'])
    D = float(current_state.get('D', 0))
    day = int(current_state['day'])

    N = float(params['population'])
    beta = float(params['beta'])
    gamma = float(params['gamma'])
    mu = float(params['mu']) # Taxa de mortalidade

    transmissao = (beta * S * I) / N
    recuperacao = gamma * I
    morte = mu * I

    S_new = S - transmissao
    I_new = I + transmissao - recuperacao - morte
    R_new = R + recuperacao
    D_new = D + morte

    return {
        'day': day + 1,
        'S': max(0, S_new),
        'I': max(0, I_new),
        'R': max(0, R_new),
        'D': max(0, D_new)
    }

SIMULATION_FUNCTIONS = {
    'SIR': run_sir,
    'SIRD': run_sird
}