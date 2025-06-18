module.exports = {
  swarm: {
    enabled: true,
    agents: {
      taskManager: { model: "claude-3-opus-20240229" },
      qualityEngineer: { model: "claude-3-sonnet-20240229" },
      deploymentSpecialist: { model: "claude-3-haiku-20240307" }
    }
  }
};
