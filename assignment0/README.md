# AutoGen SoM Assignment 0

This project demonstrates a multi-agent system using the Microsoft AutoGen Society of Mind (SoM) framework. It fulfills the requirements of Assignment 0, focusing on the integration of `UserProxyAgent` for human-in-the-loop control in both inner and outer team structures.

## Files

-   `main.py`: The main Python script containing the full implementation of the inner and outer agent teams.
-   `graph_flow.png`: A visual flow diagram of the agent architecture, illustrating the control flow and human intervention points.
-   `requirements.txt`: A list of the necessary Python packages to run this project.

## Description

The system is designed with two primary layers:

1.  **Outer Team**: A high-level team responsible for project management. It takes a user-defined task, creates a plan, and oversees the execution by the inner team. A `UserProxyAgent` is used here to approve the initial plan and validate the final output.
2.  **Inner Team (SoM)**: A specialized team encapsulated within a `SocietyOfMindAgent`. This team consists of a Developer, a Tester, and a Documentation Writer. A `UserProxyAgent` is integrated to review and approve the output at each stage (development, testing, and documentation), allowing for iterative feedback and corrections.

This implementation showcases a robust, human-supervised agentic workflow.
