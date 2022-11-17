"""
Date: 2022-11-17
By Sai Wei
Objective: modeling generalized disjunctive programming for generator switching model
Ref: Pyomo - Optimization modeling in python (chapter 11)
"""
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
# A disjunct is logically a container for the indicator variable and the 
# corresponding constraint.
def UnitCommitment():
    # Model definition
    model = pyo.ConcreteModel(name = "GeneratorSwitchModel");
    # Define the three disjuncts:
    model.NumTimePeriods = pyo.Param()
    model.GENERATORS = pyo.Set()
    model.TIME = pyo.RangeSet(model.NumTimePeriods)
    
    model.MaxPower = pyo.Param(model.GENERATORS, within = pyo.NonNegativeReals)
    model.MinPower = pyo.Param(model.GENERATORS, within = pyo.NonNegativeReals)
    model.RampUpLimit = pyo.Param(model.GENERATORS, within = pyo.NonNegativeReals)
    model.RampDownLimit = pyo.Param(model.GENERATORS, within = pyo.NonNegativeReals)
    model.StartUpRampLimit = pyo.Param(model.GENERATORS, \
                                within = pyo.NonNegativeReals)
    model.ShuntDownRampLimit = pyo.Param(model.GENERATORS, \
                                within = pyo.NonNegativeReals)
                                
    def Power_bound(m,g,t):
        return (0, m.MaxPower[g])
    model.Power = pyo.Var(model.GENERATORS, model.TIME, bounds = Power_bound)
    
    def GenOn(b,g,t):
        m = b.model()
        b.power_limit = pyo.Constraint(
            expr = pyo.inequality(m.MinPower[g], m.Power[g,t], m.MaxPower[g]))
        
        if t == m.TIME.first():
            return
        b.ramp_limit = pyo.Constraint(
            expr = pyo.inequality(-m.RampDownLimit[g], m.Power[g,t], \
            -m.MaxPower[g, t-1], m.RampUpLimit[g]))
    
    model.GenOn = Disjunct(model.GENERATORS, model.TIME, rule = GenOn)
    
    def GenOff(b,g,t):
        m = b.model()
        b.power_limit = pyo.Constraint(
            expr = m.Power[g,t]==0)
        if t == m.TIME.first():
            return
        b.ramp_limit = pyo.Constraint(
            expr = m.Power[g, t-1]<=m.ShutDownRampLimit[g])
            
    model.GenOff = Disjunct(model.GENERATORS, model.TIME, rule = GenOff)
    
    def GenStartUp(b,g,t):
        m = b.model()
        b.power_limit = pyo.Constraint(
            expr = m.Power[g,t] <=m.StartUpRampLimit[g])
    model.GenStartup = Disjunct(model.GENERATORS, model.TIME, rule =GenStartUp)
    
    # Bind the disjuncts 
    def bind_generators(m,g,t):
        return [m.GenOn[g,t], m.GenOff[g,t], m.GenStartUp[g,t]]
    model.bind_generators = Disjunction(
        model.GENERATORS, model.TIME, rule = bind_generators)
        
    # Define the switching rules for the states of generators
    def onState(m,g,t):
        if t == m.TIME.first():
            return pyo.LogicalConstraint.Skip
        return m.GenOn[g,t].indicator_var.implies(pyo.lor(
            m.GenOn[g,t-1].indicator_var,
            m.FenStartup[g,t-1].indicator_var))
    model.onState = pyo.LogicalConstraint(
        model.GENERATORS, model.TIME, rule = onState)
        
    def startupState(m,g,t):
        if t == m.TIME.first():
            return pyo.LogicalConstraint.Skip
        return m.GenStartUp[g,t].indicator_var.implies(
            m.GenOff[g,t-1].indicator_var)
    model.startupState = pyo.LogicalConstraint(
        model.GENERATORS, model.TIME, rule = startupState)
    
    return model 
