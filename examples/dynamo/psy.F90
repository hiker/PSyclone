  MODULE psy_dynamo
    USE lfric
    IMPLICIT NONE
    CONTAINS
    SUBROUTINE invoke_0(rhs)
      USE v3_kernel_mod, ONLY: rhs_v3_code
      TYPE(field_type), intent(inout) :: rhs
      INTEGER column
      INTEGER, pointer :: v3dofmap(:,:)
      TYPE(FunctionSpace_type), pointer :: rhs_space
      INTEGER nlayers
      TYPE(ColumnTopology), pointer :: topology
      SELECT TYPE ( rhs_space=>rhs%function_space )
        TYPE IS ( FunctionSpace_type )
        topology => rhs_space%topology
        nlayers = topology%layer_count()
        v3dofmap => rhs_space%dof_map(cells, fe)
      END SELECT 
      DO column=1,topology%entity_counts(cells)
        CALL rhs_v3_code(nLayers, v3dofmap(:,column), rhs%data)
      END DO 
    END SUBROUTINE invoke_0
    SUBROUTINE invoke_1(pressure_density, rhs)
      USE v3_solver_kernel_mod, ONLY: solver_v3_code
      TYPE(field_type), intent(inout) :: pressure_density, rhs
      INTEGER column
      INTEGER, pointer :: v3dofmap(:,:)
      TYPE(FunctionSpace_type), pointer :: pressure_density_space
      INTEGER nlayers
      TYPE(ColumnTopology), pointer :: topology
      SELECT TYPE ( pressure_density_space=>pressure_density%function_space )
        TYPE IS ( FunctionSpace_type )
        topology => pressure_density_space%topology
        nlayers = topology%layer_count()
        v3dofmap => pressure_density_space%dof_map(cells, fe)
      END SELECT 
      DO column=1,topology%entity_counts(cells)
        CALL solver_v3_code(nLayers, v3dofmap(:,column), pressure_density%data, rhs%data)
      END DO 
    END SUBROUTINE invoke_1
  END MODULE psy_dynamo